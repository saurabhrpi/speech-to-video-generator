"""Toggle per-template audio for Pipeline A motion-transfer (S67).

Partial Firestore update — does NOT clobber other fields. Sister script to
scripts/set_template_hero.py and scripts/set_template_nbp_regen.py.

When `audio_enabled` is True, the motion-transfer dispatcher passes
`keep_original_sound="yes"` to Kling and the output retains the driving
video's audio. Default missing/False → silent output (S66 dev/test default).

Usage:
    # Enable audio on Gangsta
    .venv/bin/python scripts/set_template_audio.py \\
        --template-id viral-dances-gangsta --enable

    # Disable
    .venv/bin/python scripts/set_template_audio.py \\
        --template-id viral-dances-gangsta --disable

    # Read current state (no write)
    .venv/bin/python scripts/set_template_audio.py \\
        --template-id viral-dances-gangsta --show
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
    ap.add_argument("--template-id", required=True, help="e.g. viral-dances-gangsta")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--enable", action="store_true", help="Set audio_enabled=true")
    grp.add_argument("--disable", action="store_true", help="Set audio_enabled=false")
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

    log.info("current  audio_enabled=%s", before.get("audio_enabled"))

    if args.show:
        return 0

    from firebase_admin import firestore as fb_firestore  # noqa: E402

    update = {
        "audio_enabled": bool(args.enable),
        "updated_at": fb_firestore.SERVER_TIMESTAMP,
    }
    _doc_ref(args.template_id).update(update)
    after = get_template(args.template_id)
    log.info("after    audio_enabled=%s", after.get("audio_enabled"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
