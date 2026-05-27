"""Seed the Firestore template registry with the High School fixture (S81).

Third template of the tiktok_dances category. Sister to
scripts/seed_pinky_up_template.py / the canonical scripts/seed_buttons_template.py.
Pipeline A (motion-onto-character via Kling Motion Control), use_nbp_regen=true
with the generic full-body framing hint.

Category: tiktok_dances (mobile label override -> "TikTok Dances").

Preview note (S81): preview generated kling-v2-6 + pro + video orientation.
Subject = different light-skinned young woman (Pattern B — source was an
identifiable real creator), going-out fit (black cropped knit + light wide-leg
jeans) at NIGHT in an urban parking lot (S81 user direction: keep light-skinned
woman + night parking-lot + going-out fit; night regen-framed per the S80 Like a
G6 lesson; feet pushed fully into frame since the source cropped them). Source
trimmed from t=0.5s to end (~15.0s), static camera.

Assets land in the S77 migrated shape directly:
  driving_video_url        -> driving_video.mp4   (high-bitrate Kling output, runtime driver)
  preview_video_url        -> preview_stream.mp4  (~5 Mbps, what the app plays)
  preview_video_url_orig   -> driving_video.mp4   (so streaming_previews --revert works)
  original_driving_video_url -> raw_source.mp4    (revert target)

After the doc write, the seed generates the first-frame poster (S81): frame0 of
preview_stream.mp4 -> thumbnail.jpg -> assets.thumbnail_url. Requires
preview_stream.mp4 to already be on R2.

Starts as DRAFT — flip to published via `scripts/set_template_status.py`.

Re-running overwrites the High School doc.

Usage:
    .venv/bin/python scripts/seed_high_school_template.py
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
from src.speech_to_video.utils.template_thumbnail import generate_thumbnail  # noqa: E402

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed_high_school_template")


TEMPLATE_ID = "viral-dances-high-school"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

_BASE = "https://assets.speech-2-video.ai/viral-dances/high-school"

HIGH_SCHOOL_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "tiktok_dances",
    "title": "High School",
    "description": "High school. 🌃✨",
    "published_status": STATUS_DRAFT,
    "assets": {
        "driving_video_url": f"{_BASE}/driving_video.mp4",
        "preview_video_url": f"{_BASE}/preview_stream.mp4",
        "preview_video_url_orig": f"{_BASE}/driving_video.mp4",
        "original_driving_video_url": f"{_BASE}/raw_source.mp4",
        "scene_image_url": None,
        "thumbnail_url": None,
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
    written = upsert_template(TEMPLATE_ID, HIGH_SCHOOL_FIXTURE)
    log.info(
        "wrote: pipeline_class=%s status=%s credit_cost=%s use_nbp_regen=%s audio_enabled=%s",
        written.get("pipeline_class"),
        written.get("published_status"),
        written.get("credit_cost"),
        written.get("use_nbp_regen"),
        written.get("audio_enabled"),
    )

    # First-frame poster (S81): extract frame0 of preview_stream.mp4 ->
    # thumbnail.jpg -> assets.thumbnail_url. force=True (fixture seeds None;
    # re-seed should rebuild). Requires preview_stream.mp4 on R2. Never fatal.
    try:
        log.info("thumbnail: %s", generate_thumbnail(written, force=True))
    except Exception as e:  # noqa: BLE001 — poster is best-effort, doc write already landed
        log.warning("thumbnail generation failed (backfill later): %s", e)

    log.info("re-reading via get_template...")
    fetched = get_template(TEMPLATE_ID)
    a = fetched.get("assets") or {}
    log.info(
        "read back: id=%s title=%s category=%s",
        fetched.get("id"), fetched.get("title"), fetched.get("category"),
    )
    log.info(
        "assets: driver=%s preview=%s orig_driver=%s thumbnail=%s",
        (a.get("driving_video_url") or "").rsplit("/", 1)[-1],
        (a.get("preview_video_url") or "").rsplit("/", 1)[-1],
        (a.get("original_driving_video_url") or "").rsplit("/", 1)[-1],
        (a.get("thumbnail_url") or "").rsplit("/", 1)[-1] or None,
    )


if __name__ == "__main__":
    main()
