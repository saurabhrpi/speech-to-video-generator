"""Flip a template's assets.driving_video_url (S74, AIV-103).

A/B mechanism for whether feeding the preview video back as the Kling driving
video produces acceptable runtime output. If yes, we can collapse the two
assets into one and eliminate the dirty-raw-source class of bug.

**Always preserves the original.** First time the script overwrites a
template's `driving_video_url`, it copies the prior value into
`assets.original_driving_video_url`. That field is never overwritten by
subsequent runs, so it always points at the true raw driver — revert is
safe across any number of flips.

Partial Firestore update — does NOT clobber other fields. Always bumps
`updated_at` so the mobile /api/templates ETag invalidates immediately
(per Memory/reference_firestore_partial_update_etag.md).

Usage — single template:
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --show
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --use-preview
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --revert
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --template-id viral-dances-smooth-criminal --set <URL>

Usage — bulk across all templates with both driving + preview URLs:
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --all --show
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --all --use-preview
    .venv/bin/python scripts/set_preview_template_driving_video.py \\
        --all --revert
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _flip_one(template_id: str, action: str, set_url: Optional[str]) -> int:
    """Apply `action` to one template. Returns exit code (0 = ok, !=0 = error)."""
    from src.speech_to_video.utils.template_registry import (  # noqa: E402
        TemplateNotFound,
        get_template,
        _doc_ref,
    )
    from firebase_admin import firestore as fb_firestore  # noqa: E402

    try:
        before = get_template(template_id)
    except TemplateNotFound:
        log.error("[%s] template_not_found", template_id)
        return 2

    assets = before.get("assets") or {}
    before_driving = assets.get("driving_video_url")
    before_preview = assets.get("preview_video_url")
    before_original = assets.get("original_driving_video_url")

    log.info("[%s] driving=%s", template_id, before_driving)
    log.info("[%s] preview=%s", template_id, before_preview)
    log.info("[%s] original=%s", template_id, before_original or "(unset)")

    if action == "show":
        return 0

    if action == "use_preview":
        if not before_preview:
            log.error("[%s] no preview_video_url; skipping", template_id)
            return 3
        new_driving = before_preview
    elif action == "set":
        new_driving = set_url  # validated by caller
    elif action == "revert":
        if not before_original:
            log.warning("[%s] no original_driving_video_url backup; nothing to revert to (skipping)", template_id)
            return 0
        new_driving = before_original
    else:
        log.error("unknown action: %s", action)
        return 1

    if new_driving == before_driving:
        log.info("[%s] no-op: requested URL matches current value", template_id)
        return 0

    update = {
        "assets.driving_video_url": new_driving,
        "updated_at": fb_firestore.SERVER_TIMESTAMP,
    }

    # First overwrite of driving_video_url for this template → capture the
    # current value as the canonical "original" backup. Idempotent: once set,
    # this field is never updated again by this script, so revert always
    # points at the true raw driver, not at a previous preview-flip value.
    if not before_original and before_driving:
        update["assets.original_driving_video_url"] = before_driving
        log.info("[%s] saving original_driving_video_url=%s", template_id, before_driving)

    _doc_ref(template_id).update(update)

    after = get_template(template_id)
    after_assets = after.get("assets") or {}
    log.info("[%s] after driving=%s", template_id, after_assets.get("driving_video_url"))
    return 0


def _list_eligible() -> List[str]:
    """Return template_ids with BOTH driving_video_url AND preview_video_url
    set. Skips templates that aren't valid candidates for the preview-as-driver
    A/B (e.g., Pipeline B templates without a preview asset, or any template
    midway through onboarding)."""
    from src.speech_to_video.utils.template_registry import list_templates  # noqa: E402

    eligible: List[str] = []
    for t in list_templates(published_only=False):
        assets = t.get("assets") or {}
        if assets.get("driving_video_url") and assets.get("preview_video_url"):
            eligible.append(t["id"])
    return sorted(eligible)


def main() -> int:
    ap = argparse.ArgumentParser()
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--template-id", help="Single template, e.g. viral-dances-smooth-criminal")
    scope.add_argument("--all", action="store_true",
                       help="Bulk: apply to every template with both driving + preview URLs")

    action = ap.add_mutually_exclusive_group(required=True)
    action.add_argument("--show", action="store_true", help="Print current state, no write")
    action.add_argument("--use-preview", action="store_true",
                        help="Set driving_video_url = preview_video_url (the A/B test)")
    action.add_argument("--revert", action="store_true",
                        help="Restore driving_video_url from original_driving_video_url backup field")
    action.add_argument("--set", dest="set_url", metavar="URL",
                        help="Set driving_video_url to an explicit URL (single-template only)")
    args = ap.parse_args()

    if args.set_url and args.all:
        ap.error("--set is single-template only; use --revert for --all")

    if args.show:
        action_name = "show"
    elif args.use_preview:
        action_name = "use_preview"
    elif args.revert:
        action_name = "revert"
    elif args.set_url:
        action_name = "set"
    else:
        ap.error("no action selected")  # unreachable; argparse enforces

    if args.template_id:
        return _flip_one(args.template_id, action_name, args.set_url)

    # --all
    ids = _list_eligible()
    log.info("found %d eligible templates: %s", len(ids), ids)
    rc = 0
    for tid in ids:
        log.info("---")
        rc |= _flip_one(tid, action_name, None)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
