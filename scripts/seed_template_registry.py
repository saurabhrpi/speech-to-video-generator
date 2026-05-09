"""Seed the template registry with the Bombale fixture (SPE-10 acceptance test).

One-shot dev script — re-running overwrites the Bombale doc. Does NOT create
assets; only writes the registry entry pointing at placeholder URLs. Real
assets land later via SPE-17 + R2 upload (SPE-12).

Usage:
    python scripts/seed_template_registry.py
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
log = logging.getLogger("seed_template_registry")


TEMPLATE_ID = "viral-dances-bombale"

BOMBALE_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "viral_dances",
    "title": "Bombale",
    "description": "Dance the Bombale.",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://placeholder.example/bombale-driving.mp4",
        "scene_image_url": None,
        "thumbnail_url": "https://placeholder.example/bombale-thumb.jpg",
        "preview_video_url": None,
    },
    "model": "kling-2.6-motion-control-image",
    "credit_cost": 23,
    "prompt_template": None,
}


def main() -> None:
    log.info("seeding template %s", TEMPLATE_ID)
    written = upsert_template(TEMPLATE_ID, BOMBALE_FIXTURE)
    log.info(
        "wrote: pipeline_class=%s status=%s credit_cost=%s",
        written.get("pipeline_class"),
        written.get("published_status"),
        written.get("credit_cost"),
    )

    log.info("re-reading via get_template...")
    fetched = get_template(TEMPLATE_ID)
    log.info(
        "read back: id=%s title=%s assets.driving=%s",
        fetched.get("id"),
        fetched.get("title"),
        (fetched.get("assets") or {}).get("driving_video_url"),
    )


if __name__ == "__main__":
    main()
