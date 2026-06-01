"""Mobile-streaming-optimized template previews (S77 stutter A/B).

The catalog's preview videos are raw Kling output at ~14-35 Mbps (1440x1440).
On a phone that bitrate can't be sustained over the network, so the player
drains its buffer and stutters (pause / start-stop). This script produces a
~5 Mbps + faststart variant and points the app at it, WITHOUT touching the
runtime Kling driver.

## Decoupling (why this is safe)

Under preview-as-driver, both `assets.preview_video_url` and
`assets.driving_video_url` point at the same high-bitrate `preview_video.mp4`.
We do NOT overwrite that file. Instead:

  --encode   : download each template's current preview, re-encode to ~5 Mbps
               + faststart, upload to a SIBLING key `preview_stream.mp4`.
  --repoint  : set preview_video_url -> preview_stream.mp4 (what the app plays),
               saving the prior value into `assets.preview_video_url_orig`.
               driving_video_url is left ALONE -> Kling driver quality intact.
  --revert   : restore preview_video_url from preview_video_url_orig.
  --show     : print current state.

Revert is a single field flip per template — no re-encode, no CF purge, no
cache games (new key = fresh fetch). Bumps updated_at so the /api/templates
ETag invalidates (Memory/reference_firestore_partial_update_etag.md).

Usage:
    .venv/bin/python scripts/streaming_previews.py --show
    .venv/bin/python scripts/streaming_previews.py --encode [--bitrate 5]
    .venv/bin/python scripts/streaming_previews.py --repoint
    .venv/bin/python scripts/streaming_previews.py --revert
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT))

import imageio_ffmpeg  # noqa: E402

from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.template_registry import (  # noqa: E402
    TemplateNotFound,
    get_template,
    list_templates,
    _doc_ref,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
STREAM_BASENAME = "preview_stream.mp4"


def _key_from_url(url: str) -> str:
    """R2 key from a public URL (strip the public base)."""
    base = r2_client.public_url("").rstrip("/")
    return url.replace(base + "/", "", 1)


def _stream_key(preview_key: str) -> str:
    return preview_key.rsplit("/", 1)[0] + "/" + STREAM_BASENAME


def _eligible(only_id: Optional[str] = None) -> List[dict]:
    """Templates that have a preview_video_url (optionally a single id)."""
    out = []
    for t in list_templates(published_only=False):
        if only_id and t["id"] != only_id:
            continue
        # Furry Friends (subject_type="animal", S89) invert the catalog twin
        # invariant: their preview is a generated PET-dance clip, NOT derived from
        # driving_video (which is a reused HUMAN driver). The driver-derived
        # encode/repoint/revert here would clobber the pet preview with the human
        # driver — so exclude animal templates from this catalog-wide tool.
        if (t.get("subject_type") or "").strip().lower() == "animal":
            continue
        if (t.get("assets") or {}).get("preview_video_url"):
            out.append(t)
    return sorted(out, key=lambda t: t["id"])


def cmd_show() -> int:
    for t in _eligible():
        a = t.get("assets") or {}
        log.info("[%s] preview=%s", t["id"], (a.get("preview_video_url") or "").rsplit("/", 1)[-1])
        log.info("[%s]   orig=%s", t["id"], (a.get("preview_video_url_orig") or "(unset)").rsplit("/", 1)[-1])
        log.info("[%s] driver=%s", t["id"], (a.get("driving_video_url") or "").rsplit("/", 1)[-1])
    return 0


def cmd_encode(bitrate_mbps: float) -> int:
    rc = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for t in _eligible():
            tid = t["id"]
            a = t.get("assets") or {}
            # Encode from the ORIGINAL preview, even if already repointed.
            src_url = a.get("preview_video_url_orig") or a.get("preview_video_url")
            preview_key = _key_from_url(a.get("preview_video_url_orig") or a.get("preview_video_url"))
            stream_key = _stream_key(preview_key)

            log.info("[%s] download %s", tid, src_url)
            src_path = tmp / f"{tid}_src.mp4"
            try:
                with requests.get(src_url, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(src_path, "wb") as f:
                        for chunk in r.iter_content(64 * 1024):
                            f.write(chunk)
            except Exception as e:
                log.error("[%s] download FAILED: %s", tid, e)
                rc = 1
                continue

            out_path = tmp / f"{tid}_stream.mp4"
            br = f"{bitrate_mbps:g}M"
            maxrate = f"{bitrate_mbps * 1.2:g}M"
            bufsize = f"{bitrate_mbps * 2.4:g}M"
            cmd = [
                FFMPEG, "-y", "-i", str(src_path),
                "-c:v", "libx264", "-profile:v", "high", "-preset", "medium",
                "-b:v", br, "-maxrate", maxrate, "-bufsize", bufsize,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart",
                str(out_path),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0 or not out_path.exists():
                log.error("[%s] ffmpeg FAILED: %s", tid, proc.stderr[-400:])
                rc = 1
                continue

            src_mb = src_path.stat().st_size / 1048576
            out_mb = out_path.stat().st_size / 1048576
            url = r2_client.upload_file(str(out_path), stream_key)
            log.info("[%s] %.1f MB -> %.1f MB  uploaded %s", tid, src_mb, out_mb, url)
    return rc


def _repoint_one(tid: str, revert: bool) -> int:
    from firebase_admin import firestore as fb_firestore
    try:
        t = get_template(tid)
    except TemplateNotFound:
        log.error("[%s] not found", tid)
        return 2
    a = t.get("assets") or {}
    cur = a.get("preview_video_url")
    orig = a.get("preview_video_url_orig")

    if revert:
        if not orig:
            log.warning("[%s] no preview_video_url_orig backup; skipping", tid)
            return 0
        new = orig
        update = {"assets.preview_video_url": new, "updated_at": fb_firestore.SERVER_TIMESTAMP}
    else:
        stream_key = _stream_key(_key_from_url(orig or cur))
        new = r2_client.public_url(stream_key)
        if new == cur:
            log.info("[%s] already pointed at stream", tid)
            return 0
        update = {"assets.preview_video_url": new, "updated_at": fb_firestore.SERVER_TIMESTAMP}
        if not orig:
            update["assets.preview_video_url_orig"] = cur
            log.info("[%s] saving preview_video_url_orig=%s", tid, cur.rsplit("/", 1)[-1])

    _doc_ref(tid).update(update)
    log.info("[%s] preview_video_url -> %s", tid, new.rsplit("/", 1)[-1])
    return 0


def cmd_repoint(revert: bool) -> int:
    rc = 0
    for t in _eligible():
        rc |= _repoint_one(t["id"], revert)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--show", action="store_true")
    g.add_argument("--encode", action="store_true", help="Build + upload preview_stream.mp4 for all")
    g.add_argument("--repoint", action="store_true", help="Point preview_video_url at the stream file")
    g.add_argument("--revert", action="store_true", help="Restore preview_video_url from backup")
    ap.add_argument("--bitrate", type=float, default=5.0, help="Target video Mbps (default 5)")
    args = ap.parse_args()

    if args.show:
        return cmd_show()
    if args.encode:
        return cmd_encode(args.bitrate)
    if args.repoint:
        return cmd_repoint(revert=False)
    if args.revert:
        return cmd_repoint(revert=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
