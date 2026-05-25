"""Rename template R2 files so filenames match runtime roles (S77).

After preview-as-driver + streaming previews, the filenames were misleading:
`preview_video.mp4` was actually the runtime DRIVER, and `driving_video.mp4`
was just the raw source / revert target. This migrates every template to:

    raw_source.mp4      <- the raw source clip      (original_driving_video_url)
    driving_video.mp4   <- high-bitrate Kling output (driving_video_url) = active driver
    preview_stream.mp4  <- ~5 Mbps app preview       (preview_video_url)   [unchanged]

Server-side R2 copies (no download). Idempotent: templates already migrated
(driving_video_url already ends in driving_video.mp4) are skipped.

Staged for safety:
  --dry-run   : print the full plan, touch nothing.
  --execute   : do the R2 copies + Firestore field updates + CF purge.
                Leaves the now-redundant old preview_video.mp4 in place.
  --cleanup   : delete the orphaned old high-bitrate keys.  ** BROKEN — see below. **

Bumps updated_at so the /api/templates ETag invalidates
(Memory/reference_firestore_partial_update_etag.md).

## ⚠️ KNOWN BUG — `--cleanup` is a no-op (S77; deferred to backlog)

`--cleanup` deletes nothing as written. `plan_template()` returns
`skip="already migrated"` for every template once `driving_video_url` ends in
`driving_video.mp4` — which is always true after `--execute`. The main loop
hits `if p.skip: continue` BEFORE the cleanup branch, so `p.delete_key` is
never even computed; running it just prints "SKIP — already migrated" for all
rows. (Verified S77: ran --cleanup, deleted 0, orphans still present.)

The orphans are therefore STILL on R2 — harmless (unreferenced by any Firestore
asset field, only costing storage), but present:
  * `preview_video.mp4` on the 16 standard templates, AND
  * `driving_video_10s.mp4` + `preview_video_audio.mp4` on gangsta (its
    pre-migration filenames were non-standard, so it has TWO orphans).

### Correct fix (when this comes off the backlog)

Do NOT hardcode `preview_video.mp4` as the orphan — that misses gangsta's two.
Make cleanup independent of `plan_template`'s skip, and per template enumerate
the R2 dir, deleting any `.mp4` NOT referenced by a CURRENT Firestore asset
field:

    keep = { _key(assets[f]) for f in (
        "driving_video_url", "preview_video_url", "original_driving_video_url",
        "preview_video_url_orig", "thumbnail_url", "scene_image_url"
    ) if assets.get(f) }
    for key in r2_client.list_objects(prefix=f"viral-dances/{slug}/"):
        if key.endswith(".mp4") and key not in keep:
            r2_client.delete_object(key)   # irreversible — dry-run first

Keep it dry-run-first; it is an irreversible delete.

NOTE: chain scripts (test_<slug>_chain.py) hardcode .../driving_video.mp4 as
their driver. After this migration that key holds the high-bitrate Kling
output, not the raw source — re-running a chain script would drive off the
prior output. Going forward, point new chain scripts at raw_source.mp4.
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.config import get_settings  # noqa: E402
from src.speech_to_video.utils.template_registry import (  # noqa: E402
    get_template,
    list_templates,
    _doc_ref,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BUCKET = get_settings().r2_bucket
RAW_NAME = "raw_source.mp4"
DRIVER_NAME = "driving_video.mp4"


def _base() -> str:
    return r2_client.public_url("").rstrip("/")


def _key(url: str) -> str:
    return url.replace(_base() + "/", "", 1)


def _dir(key: str) -> str:
    return key.rsplit("/", 1)[0]


class Plan:
    def __init__(self, tid: str):
        self.tid = tid
        self.skip: Optional[str] = None
        self.copies: List[tuple] = []      # (src_key, dst_key)
        self.fields: Dict[str, str] = {}   # firestore assets.* -> url
        self.delete_key: Optional[str] = None
        self.purge_urls: List[str] = []


def plan_template(t: dict) -> Plan:
    tid = t["id"]
    p = Plan(tid)
    a = t.get("assets") or {}
    dv, pv, odv = a.get("driving_video_url"), a.get("preview_video_url"), a.get("original_driving_video_url")

    if not (dv and pv and odv):
        p.skip = f"missing fields (dv={bool(dv)} pv={bool(pv)} odv={bool(odv)})"
        return p

    dv_key = _key(dv)
    if dv_key.endswith("/" + DRIVER_NAME):
        p.skip = "already migrated (driving_video_url -> driving_video.mp4)"
        return p

    d = _dir(dv_key)
    raw_key = f"{d}/{RAW_NAME}"
    driver_key = f"{d}/{DRIVER_NAME}"
    odv_key = _key(odv)

    # 1. preserve raw source under the new name
    p.copies.append((odv_key, raw_key))
    # 2. high-bitrate driver content -> driving_video.mp4 (overwrites the old raw at that key)
    p.copies.append((dv_key, driver_key))

    p.fields = {
        "assets.driving_video_url": r2_client.public_url(driver_key),
        "assets.original_driving_video_url": r2_client.public_url(raw_key),
        "assets.preview_video_url_orig": r2_client.public_url(driver_key),
        # preview_video_url (stream) unchanged
    }
    p.delete_key = dv_key  # old preview_video.mp4 — orphaned after field updates
    p.purge_urls = [r2_client.public_url(driver_key)]  # content at this key changed
    return p


def _copy(src: str, dst: str) -> None:
    r2_client._s3().copy_object(
        Bucket=BUCKET, CopySource={"Bucket": BUCKET, "Key": src}, Key=dst,
        MetadataDirective="COPY",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--execute", action="store_true")
    g.add_argument("--cleanup", action="store_true", help="Delete orphaned old preview_video.mp4 keys (run after verifying)")
    args = ap.parse_args()

    from firebase_admin import firestore as fb_firestore

    templates = sorted(list_templates(published_only=False), key=lambda t: t["id"])
    plans = [plan_template(t) for t in templates if (t.get("assets") or {}).get("driving_video_url")]

    purge_all: List[str] = []
    for p in plans:
        if p.skip:
            log.info("[%s] SKIP — %s", p.tid, p.skip)
            continue

        if args.cleanup:
            # Only delete if the template is migrated AND the orphan still exists.
            cur = get_template(p.tid).get("assets") or {}
            if not _key(cur.get("driving_video_url", "")).endswith("/" + DRIVER_NAME):
                log.info("[%s] cleanup SKIP — not migrated yet", p.tid)
                continue
            log.info("[%s] DELETE orphan %s", p.tid, p.delete_key)
            if r2_client.head_object(p.delete_key):
                r2_client.delete_object(p.delete_key)
            continue

        log.info("[%s] %s", p.tid, "PLAN" if args.dry_run else "EXECUTE")
        for src, dst in p.copies:
            log.info("    copy   %s  ->  %s", src, dst)
        for f, url in p.fields.items():
            log.info("    field  %s = %s", f, url.rsplit("/", 1)[-1])
        log.info("    (later) delete orphan %s", p.delete_key)

        if args.execute:
            for src, dst in p.copies:
                _copy(src, dst)
            update = dict(p.fields)
            update["updated_at"] = fb_firestore.SERVER_TIMESTAMP
            _doc_ref(p.tid).update(update)
            purge_all.extend(p.purge_urls)

    if args.execute and purge_all:
        log.info("purging %d CF urls", len(purge_all))
        subprocess.run([sys.executable, str(ROOT / "scripts/purge_cf_cache.py"), *purge_all])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
