"""Flip a template's assets.driving_video_url (S74).

Used to A/B whether feeding the preview video back as the Kling driving
video produces acceptable output. If yes, we can collapse the two assets
into one and eliminate the dirty-raw-source class of bug (see Smooth Criminal
v3+pro failure: TikTok UI overlays in the raw driver leaked into Kling output).

Partial Firestore update — does NOT clobber other fields. Always bumps
`updated_at` so the mobile /api/templates ETag invalidates immediately
(per Memory/reference_firestore_partial_update_etag.md).

Usage:
    # Print current state (driving + preview URLs side-by-side, no write)
    .venv/bin/python scripts/set_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --show

    # Point driving at the preview video (the A/B test)
    .venv/bin/python scripts/set_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --use-preview

    # Set to an explicit URL (used to revert)
    .venv/bin/python scripts/set_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal \\
        --set https://assets.speech-2-video.ai/viral-dances/smooth-criminal/driving_video.mp4
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template-id", required=True, help="e.g. viral-dances-smooth-criminal")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--use-preview", action="store_true",
                     help="Set driving_video_url = preview_video_url (A/B test)")
    grp.add_argument("--set", dest="set_url", metavar="URL",
                     help="Set driving_video_url to an explicit URL (revert path)")
    grp.add_argument("--show", action="store_true", help="Print current state, no write")
    args = ap.parse_args()

    from src.speech_to_video.utils.template_registry import (  # noqa: E402
        TemplateNotFound,
        get_template,
        _doc_ref,
    )

    try:
        before = get_template(args.template_id)
    except TemplateNotFound:
        log.error("template_not_found: %s", args.template_id)
        return 2

    before_assets = before.get("assets") or {}
    before_driving = before_assets.get("driving_video_url")
    before_preview = before_assets.get("preview_video_url")
    log.info("current  driving_video_url=%s", before_driving)
    log.info("current  preview_video_url=%s", before_preview)

    if args.show:
        return 0

    if args.use_preview:
        if not before_preview:
            log.error("template has no preview_video_url; cannot point driving at it")
            return 3
        new_driving = before_preview
    else:
        new_driving = args.set_url

    if new_driving == before_driving:
        log.info("no-op: requested URL matches current value, skipping write")
        return 0

    from firebase_admin import firestore as fb_firestore  # noqa: E402

    # Nested-field update via dotted path; preserves the rest of assets.
    update = {
        "assets.driving_video_url": new_driving,
        "updated_at": fb_firestore.SERVER_TIMESTAMP,
    }
    _doc_ref(args.template_id).update(update)

    after = get_template(args.template_id)
    log.info("after    driving_video_url=%s", (after.get("assets") or {}).get("driving_video_url"))
    log.info("(revert with: --set %s)", before_driving)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
