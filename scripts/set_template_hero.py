"""Toggle V2 home hero-carousel inclusion for a single template.

S66 — partial Firestore update; does NOT clobber other fields. Sister script
to scripts/set_template_nbp_regen.py. Use this to add or remove templates
from the landscape "Top Trends" hero carousel on the V2 home screen.

Usage:
    # Add Bombale to hero, first position
    .venv/bin/python scripts/set_template_hero.py \\
        --template-id viral-dances-bombale \\
        --enable --order 0

    # Remove from hero
    .venv/bin/python scripts/set_template_hero.py \\
        --template-id viral-dances-bombale --disable

    # Read current state (no write)
    .venv/bin/python scripts/set_template_hero.py \\
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
    grp.add_argument("--enable", action="store_true", help="Set is_hero=true")
    grp.add_argument("--disable", action="store_true", help="Set is_hero=false")
    grp.add_argument("--show", action="store_true", help="Print current state, no write")
    ap.add_argument(
        "--order",
        type=int,
        default=None,
        help="hero_order (asc; ties break on title). Only applied with --enable.",
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
        "current  is_hero=%s  hero_order=%s",
        before.get("is_hero"),
        before.get("hero_order"),
    )

    if args.show:
        return 0

    from firebase_admin import firestore as fb_firestore  # noqa: E402

    update: dict = {
        "is_hero": bool(args.enable),
        "updated_at": fb_firestore.SERVER_TIMESTAMP,
    }
    if args.enable and args.order is not None:
        update["hero_order"] = args.order

    _doc_ref(args.template_id).update(update)
    after = get_template(args.template_id)
    log.info(
        "after    is_hero=%s  hero_order=%s",
        after.get("is_hero"),
        after.get("hero_order"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
