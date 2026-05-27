"""Generate first-frame poster thumbnails for template tiles (S80).

Mobile home tiles play a <Video> only while on-screen (to bound iOS decoders).
Off-screen / not-yet-loaded tiles show a STATIC first-frame image so the grid is
never black — matching the competitor's "paused = first frame" look. This script
extracts frame 0 of each published template's preview, uploads it as
`thumbnail.jpg` next to the video, and points the Firestore `assets.thumbnail_url`
at it (partial update so sibling asset fields are untouched; bumps updated_at so
the /api/templates ETag changes and mobile pulls fresh — see
Memory/reference_firestore_partial_update_etag.md).

Thumbnail = frame 0 of the PREVIEW (what the tile video starts on), so the
poster→video handoff is seamless.

Usage:
    .venv/bin/python scripts/generate_template_thumbnails.py --dry-run
    .venv/bin/python scripts/generate_template_thumbnails.py            # missing only
    .venv/bin/python scripts/generate_template_thumbnails.py --force     # regenerate all
    .venv/bin/python scripts/generate_template_thumbnails.py --template-id viral-dances-woman
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.template_registry import (  # noqa: E402
    list_templates,
    _doc_ref,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gen_thumbs")

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
THUMB_WIDTH = 720  # shared by tile (~530px @3x) and hero; -2 keeps aspect


def _public_base() -> str:
    return r2_client.public_url("").rstrip("/")


def _key_prefix(asset_url: str) -> str | None:
    """viral-dances/<slug> from a public asset URL, or None."""
    base = _public_base() + "/"
    if not asset_url or not asset_url.startswith(base):
        return None
    key = asset_url[len(base):]            # viral-dances/<slug>/preview_stream.mp4
    return key.rsplit("/", 1)[0]           # viral-dances/<slug>


def _extract_frame0(src_url: str, out_path: Path) -> bool:
    cmd = [
        FFMPEG, "-y", "-ss", "0", "-i", src_url, "-frames:v", "1",
        "-vf", f"scale={THUMB_WIDTH}:-2", "-q:v", "3", str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        log.error("ffmpeg failed: %s", r.stderr.strip().splitlines()[-1:] or r.returncode)
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate even if thumbnail_url already set")
    ap.add_argument("--template-id", help="only this template")
    args = ap.parse_args()

    from firebase_admin import firestore as fb_firestore

    templates = list_templates(published_only=True)
    if args.template_id:
        templates = [t for t in templates if t["id"] == args.template_id]

    done = skipped = failed = 0
    with tempfile.TemporaryDirectory() as td:
        for t in templates:
            tid = t["id"]
            a = t.get("assets") or {}
            existing = a.get("thumbnail_url") or ""
            # A placeholder.example or non-http value is NOT a real thumbnail —
            # treat it as missing so it gets generated even without --force.
            usable_existing = existing.startswith("http") and "placeholder.example" not in existing
            if usable_existing and not args.force:
                log.info("SKIP %s (already has usable thumbnail_url)", tid)
                skipped += 1
                continue
            src = a.get("preview_video_url") or a.get("driving_video_url")
            prefix = _key_prefix(src or "")
            if not prefix:
                log.warning("SKIP %s (no usable R2 asset url: %s)", tid, src)
                skipped += 1
                continue
            thumb_key = f"{prefix}/thumbnail.jpg"
            thumb_url = r2_client.public_url(thumb_key)

            if args.dry_run:
                log.info("DRY %s  frame0(%s) -> %s", tid, src.rsplit("/", 1)[-1], thumb_key)
                done += 1
                continue

            out = Path(td) / f"{tid}.jpg"
            if not _extract_frame0(src, out):
                failed += 1
                continue
            r2_client.upload_file(str(out), thumb_key, content_type="image/jpeg")
            _doc_ref(tid).update({
                "assets.thumbnail_url": thumb_url,
                "updated_at": fb_firestore.SERVER_TIMESTAMP,
            })
            log.info("OK   %s -> %s (%d bytes)", tid, thumb_key, out.stat().st_size)
            done += 1

    log.info("done=%d skipped=%d failed=%d", done, skipped, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
