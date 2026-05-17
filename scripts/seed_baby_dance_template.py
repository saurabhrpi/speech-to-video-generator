"""Seed the Firestore template registry with the Baby Dance fixture (S67).

Sister to scripts/seed_gangsta_template.py. Pipeline A (motion-onto-character
via Kling Motion Control), use_nbp_regen=true with the same generic full-body
framing hint used for Bombale and Gangsta.

Starts as DRAFT — flip to published via `scripts/set_template_status.py` once
sim-tested E2E with a real selfie. Hero inclusion is a separate write
(`scripts/set_template_hero.py --enable --order N`).

Re-running overwrites the Baby Dance doc.

Usage:
    .venv/bin/python scripts/seed_baby_dance_template.py
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
log = logging.getLogger("seed_baby_dance_template")


TEMPLATE_ID = "viral-dances-baby-dance"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

BABY_DANCE_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "viral_dances",
    "title": "Baby Dance",
    "description": "Tiny moves, big charm — pure fun in motion!",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://assets.speech-2-video.ai/viral-dances/baby-dance/driving_video_10s.mp4",
        "scene_image_url": None,
        "thumbnail_url": "https://assets.speech-2-video.ai/viral-dances/baby-dance/thumbnail.jpg",
        "preview_video_url": "https://assets.speech-2-video.ai/viral-dances/baby-dance/preview_video.mp4",
    },
    "model": "kling-2.6-motion-control-image",
    "credit_cost": 23,
    "prompt_template": GENERIC_KLING_PROMPT,
    "use_nbp_regen": True,
    "nbp_framing_hint": "Composition: full body standing pose, head to feet.",
    "is_hero": False,
    "hero_order": None,
}


def main() -> None:
    log.info("seeding template %s", TEMPLATE_ID)
    written = upsert_template(TEMPLATE_ID, BABY_DANCE_FIXTURE)
    log.info(
        "wrote: pipeline_class=%s status=%s credit_cost=%s use_nbp_regen=%s",
        written.get("pipeline_class"),
        written.get("published_status"),
        written.get("credit_cost"),
        written.get("use_nbp_regen"),
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
