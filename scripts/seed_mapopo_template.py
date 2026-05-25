"""Seed the Firestore template registry with the Mapopo fixture (S77).

Sister to scripts/seed_na_favelinha_template.py. Pipeline A
(motion-onto-character via Kling Motion Control), use_nbp_regen=true with
the generic full-body framing hint.

Category: viral_dances (mechanically title-cases to "Viral Dances" in
mobile, no CATEGORY_LABEL_OVERRIDES entry needed).

Preview note (S77): subject = recolored toddler girl (NBP v1 + clothing
recolor pass). Driver was 2x-upscaled via Replicate Real-ESRGAN (2552x2560),
then re-timed back to the original 9.45s + original audio re-muxed (the
upscaler had stretched it to 13.81s). Preview generated kling-v2-6 + pro +
video orientation from that synced upscaled driver. Uploaded raw.

Starts as DRAFT — flip to published via `scripts/set_template_status.py`.

Re-running overwrites the Mapopo doc.

Usage:
    .venv/bin/python scripts/seed_mapopo_template.py
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
log = logging.getLogger("seed_mapopo_template")


TEMPLATE_ID = "viral-dances-mapopo"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

MAPOPO_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "viral_dances",
    "title": "Mapopo",
    "description": "Tiny dancer, big moves. 👶",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://assets.speech-2-video.ai/viral-dances/mapopo/driving_video.mp4",
        "scene_image_url": None,
        "thumbnail_url": None,
        "preview_video_url": "https://assets.speech-2-video.ai/viral-dances/mapopo/preview_video.mp4",
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
    written = upsert_template(TEMPLATE_ID, MAPOPO_FIXTURE)
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
