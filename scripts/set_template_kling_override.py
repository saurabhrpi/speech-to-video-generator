"""Per-template Kling model/mode override (S74, AIV-101).

Wins over the global config (config/runtime). Use for templates whose
driving video makes them sensitive to model choice — e.g. Smooth Criminal
needs v2.6 because its raw driver has burned-in TikTok UI overlays that
v3 latches onto but v2.6 tolerates.

Cleared templates fall back to the global runtime config automatically.

Sister scripts:
  scripts/set_kling_runtime.py            — global default
  scripts/set_template_audio.py           — audio_enabled
  scripts/set_template_driving_video.py   — driving_video_url (S74 A/B)

Usage:
    # Show current override state for one template
    .venv/bin/python scripts/set_template_kling_override.py \\
        --template-id viral-dances-smooth-criminal --show

    # Pin SC to v2.6 std (overrides whatever global is)
    .venv/bin/python scripts/set_template_kling_override.py \\
        --template-id viral-dances-smooth-criminal --model kling-v2-6 --mode std

    # Override just one dimension (model only or mode only)
    .venv/bin/python scripts/set_template_kling_override.py \\
        --template-id viral-dances-smooth-criminal --model kling-v2-6

    # Remove override; template falls back to global
    .venv/bin/python scripts/set_template_kling_override.py \\
        --template-id viral-dances-smooth-criminal --clear
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

VALID_MODELS = {"kling-v2-6", "kling-v3"}
VALID_MODES = {"std", "pro"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template-id", required=True, help="e.g. viral-dances-smooth-criminal")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--show", action="store_true", help="Print current overrides, no write")
    grp.add_argument("--clear", action="store_true", help="Remove both overrides; template falls back to global")
    grp.add_argument("--model", choices=sorted(VALID_MODELS), help="Set kling_model_override")
    ap.add_argument("--mode", choices=sorted(VALID_MODES), help="Set kling_mode_override (combine with --model, or use alone)")
    args = ap.parse_args()

    # Allow --mode alone without --model (mutually-exclusive group covers --model alone)
    if not args.show and not args.clear and not args.model and not args.mode:
        ap.error("provide at least one of --model / --mode (or --show / --clear)")

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

    log.info("current  kling_model_override=%s", before.get("kling_model_override"))
    log.info("current  kling_mode_override=%s",  before.get("kling_mode_override"))

    if args.show:
        return 0

    from firebase_admin import firestore as fb_firestore  # noqa: E402

    update = {"updated_at": fb_firestore.SERVER_TIMESTAMP}

    if args.clear:
        # firestore.DELETE_FIELD removes the field rather than nulling it,
        # so the resolver's `template.get("kling_model_override") or globals_cfg[...]`
        # short-circuit works correctly (None and missing both fall through).
        update["kling_model_override"] = fb_firestore.DELETE_FIELD
        update["kling_mode_override"] = fb_firestore.DELETE_FIELD
    else:
        if args.model:
            update["kling_model_override"] = args.model
        if args.mode:
            update["kling_mode_override"] = args.mode

    _doc_ref(args.template_id).update(update)
    after = get_template(args.template_id)
    log.info("after    kling_model_override=%s", after.get("kling_model_override"))
    log.info("after    kling_mode_override=%s",  after.get("kling_mode_override"))
    log.info("(takes up to 30s to propagate via backend cache TTL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
