"""Toggle Pipeline A NBP regen on/off for a single template.

S66 — partial Firestore update; does NOT clobber other fields (the existing
`scripts/seed_template_registry.py` uses set() which would overwrite the
template's prompt_template, assets, etc.). Use this for per-template rollout
of the NBP regen step after eyeballing quality on the sim.

Usage:
    # Turn on for Bombale with a framing hint
    .venv/bin/python scripts/set_template_nbp_regen.py \\
        --template-id viral-dances-bombale \\
        --enable \\
        --framing-hint "Composition: full body standing pose, head to feet."

    # Turn off
    .venv/bin/python scripts/set_template_nbp_regen.py \\
        --template-id viral-dances-bombale --disable

    # Read current state (no write)
    .venv/bin/python scripts/set_template_nbp_regen.py \\
        --template-id viral-dances-bombale --show
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
    ap.add_argument("--template-id", required=True, help="e.g. viral-dances-bombale")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--enable", action="store_true", help="Set use_nbp_regen=true")
    grp.add_argument("--disable", action="store_true", help="Set use_nbp_regen=false")
    grp.add_argument("--show", action="store_true", help="Print current state, no write")
    ap.add_argument(
        "--framing-hint",
        default=None,
        help="Per-template NBP framing hint. Only applied with --enable. "
        "Pass empty string to clear an existing hint.",
    )
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

    log.info(
        "current  use_nbp_regen=%s  nbp_framing_hint=%r",
        before.get("use_nbp_regen"),
        before.get("nbp_framing_hint"),
    )

    if args.show:
        return 0

    from firebase_admin import firestore as fb_firestore  # noqa: E402

    update: dict = {
        "use_nbp_regen": bool(args.enable),
        "updated_at": fb_firestore.SERVER_TIMESTAMP,
    }
    if args.enable and args.framing_hint is not None:
        update["nbp_framing_hint"] = args.framing_hint  # empty string clears

    _doc_ref(args.template_id).update(update)
    after = get_template(args.template_id)
    log.info(
        "after    use_nbp_regen=%s  nbp_framing_hint=%r",
        after.get("use_nbp_regen"),
        after.get("nbp_framing_hint"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
