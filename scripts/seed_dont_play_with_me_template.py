"""Seed the Firestore template registry with the Don't Play With Me fixture (S76).

Sister to scripts/seed_boot_stop_working_template.py. Pipeline A
(motion-onto-character via Kling Motion Control), use_nbp_regen=true with
the generic full-body framing hint.

Category: iconic_dances (row introduced S75 — mechanically title-cases to
"Iconic Dances" in mobile, no CATEGORY_LABEL_OVERRIDES entry needed).

Preview note (S76): the preview was generated with kling-v3 + pro + video
orientation, then audio-corrected with a +0.5s ffmpeg -itsoffset delay and
its silent head trimmed (the Kling MC audio-lead artifact — see
Memory/feedback_kling_audio_lead_and_preview_propagation.md). Runtime user
gens may need the same +0.5s shift; pending verification (Task 4 / AIV).

Starts as DRAFT — flip to published via `scripts/set_template_status.py`
once sim-tested E2E with a real selfie.

Re-running overwrites the Don't Play With Me doc.

Usage:
    .venv/bin/python scripts/seed_dont_play_with_me_template.py
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
log = logging.getLogger("seed_dont_play_with_me_template")


TEMPLATE_ID = "viral-dances-dont-play-with-me"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

DONT_PLAY_WITH_ME_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "iconic_dances",
    "title": "Don't Play With Me",
    "description": "Full attitude, zero chill. 💅",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://assets.speech-2-video.ai/viral-dances/dont-play-with-me/driving_video.mp4",
        "scene_image_url": None,
        "thumbnail_url": None,
        "preview_video_url": "https://assets.speech-2-video.ai/viral-dances/dont-play-with-me/preview_video.mp4",
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
    written = upsert_template(TEMPLATE_ID, DONT_PLAY_WITH_ME_FIXTURE)
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
        "read back: id=%s title=%s category=%s assets.preview=%s",
        fetched.get("id"),
        fetched.get("title"),
        fetched.get("category"),
        (fetched.get("assets") or {}).get("preview_video_url"),
    )


if __name__ == "__main__":
    main()
