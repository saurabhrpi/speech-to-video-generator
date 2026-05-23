"""Seed the Firestore template registry with the Smooth Criminal fixture (S72).

Sister to scripts/seed_bad_template.py. Pipeline A (motion-onto-character
via Kling Motion Control), use_nbp_regen=true with the same generic full-body
framing hint we use for Bombale, Gangsta, Baby Dance, Beat It, and Bad.

Category: mj_dances (third MJ template, with Beat It and Bad).

Starts as DRAFT — flip to published via `scripts/set_template_status.py` once
sim-tested E2E with a real selfie. Hero inclusion is a separate write
(`scripts/set_template_hero.py --enable --order N`).

Re-running overwrites the Smooth Criminal doc.

Usage:
    .venv/bin/python scripts/seed_smooth_criminal_template.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils.template_registry import (  # noqa: E402
    OUTCOME_ONTO_CHARACTER,
    PIPELINE_MOTION_TRANSFER,
    STATUS_DRAFT,
    get_template,
    upsert_template,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed_smooth_criminal_template")


TEMPLATE_ID = "viral-dances-smooth-criminal"

# Generic coherence prompt — identical across all Pipeline A templates.
# Per-template specifics live in nbp_framing_hint, not in this string
# (Memory/feedback_no_overfit_prompts.md).
GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

SMOOTH_CRIMINAL_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "mj_dances",
    "title": "Smooth Criminal",
    "description": "Smooth footwork, iconic lean, stylish energy. 🕺⚡",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://assets.speech-2-video.ai/viral-dances/smooth-criminal/driving_video.mp4",
        "scene_image_url": None,
        "thumbnail_url": None,
        "preview_video_url": "https://assets.speech-2-video.ai/viral-dances/smooth-criminal/preview_video.mp4",
    },
    "model": "kling-2.6-motion-control-image",
    "credit_cost": 25,
    "prompt_template": GENERIC_KLING_PROMPT,
    "use_nbp_regen": True,
    "nbp_framing_hint": "Composition: full body standing pose, head to feet.",
    "audio_enabled": True,
    "is_hero": False,
    "hero_order": None,
}


def main() -> None:
    log.info("seeding template %s", TEMPLATE_ID)
    written = upsert_template(TEMPLATE_ID, SMOOTH_CRIMINAL_FIXTURE)
    log.info(
        "wrote: pipeline_class=%s status=%s credit_cost=%s use_nbp_regen=%s audio_enabled=%s",
        written.get("pipeline_class"),
        written.get("published_status"),
        written.get("credit_cost"),
        written.get("use_nbp_regen"),
        written.get("audio_enabled"),
    )

    log.info("re-reading via get_template...")
    fetched = get_template(TEMPLATE_ID)
    log.info(
        "read back: id=%s title=%s assets.preview=%s",
        fetched.get("id"),
        fetched.get("title"),
        (fetched.get("assets") or {}).get("preview_video_url"),
    )


if __name__ == "__main__":
    main()
