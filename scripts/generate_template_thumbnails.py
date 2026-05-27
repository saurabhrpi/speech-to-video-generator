"""Generate first-frame poster thumbnails for template tiles (S80; S81 refactor).

Catalog-wide BACKFILL tool. The per-template core now lives in
`src/speech_to_video/utils/template_thumbnail.generate_thumbnail` so the seed
scripts can produce a poster inline (a new template auto-gets its thumbnail).
This script just loops that helper over published templates.

Mobile home tiles play a <Video> only while on-screen (to bound iOS decoders).
Off-screen / not-yet-loaded tiles show a STATIC first-frame image so the grid is
never black — matching the competitor's "paused = first frame" look. Thumbnail =
frame 0 of the PREVIEW (what the tile video starts on), so the poster→video
handoff is seamless. See template_thumbnail.py for the mechanics.

Usage:
    .venv/bin/python scripts/generate_template_thumbnails.py --dry-run
    .venv/bin/python scripts/generate_template_thumbnails.py            # missing only
    .venv/bin/python scripts/generate_template_thumbnails.py --force     # regenerate all
    .venv/bin/python scripts/generate_template_thumbnails.py --template-id viral-dances-woman
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils.template_registry import list_templates  # noqa: E402
from src.speech_to_video.utils.template_thumbnail import generate_thumbnail  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gen_thumbs")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="regenerate even if thumbnail_url already set")
    ap.add_argument("--template-id", help="only this template (must be published)")
    args = ap.parse_args()

    templates = list_templates(published_only=True)
    if args.template_id:
        templates = [t for t in templates if t["id"] == args.template_id]

    counts = {"ok": 0, "skipped": 0, "failed": 0}
    for t in templates:
        counts[generate_thumbnail(t, force=args.force, dry_run=args.dry_run)] += 1

    log.info("done=%d skipped=%d failed=%d", counts["ok"], counts["skipped"], counts["failed"])
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
