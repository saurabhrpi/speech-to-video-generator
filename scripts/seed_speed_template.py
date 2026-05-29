"""Seed the Firestore template registry with the Speed fixture (S83).

Fourteenth template of the tiktok_dances category. Sister to
scripts/seed_seteadora_template.py / the canonical
scripts/seed_buttons_template.py.

Category: tiktok_dances (mobile label override -> "TikTok Dances").

Preview note (S83): Pattern B holistic regen — DIFFERENT South Asian man, dark
hair, athletic, on an EMPTY HIGHWAY AT NIGHT (open road, vanishing-point lane
markings, distant taillights, streetlamps along the shoulder). Source was an
empty suburban street at night (close register to High School / parking lot),
so per S83 user direction the regen relocated him to an open highway.

Shoulder re-roll (S83): the first NBP edit placed the subject in the MIDDLE
of the highway road. Per S83 user direction, Pattern A re-edit moved the road
to the right of the frame and the subject onto the gravel/grass SHOULDER on
the left — so he isn't standing on lane markings.

Wardrobe = black pullover hoodie + olive cargo trousers + chunky sneakers
(source = dark gray hoodie + black cargo). Same streetwear silhouette, swapped
color register. Source trimmed to 15s from a 0.5s start.

AUDIO-LEAD: not applied this template — user verified the roll's audio was
already in sync (the Kling MC v2.6+pro+video audio-lead is per-gen-variable per
Memory/feedback_kling_audio_lead_and_preview_propagation.md). Driver = raw
Kling output (no re-encode); preview = ~5 Mbps re-encode of the same source.

Assets land in the S77 migrated shape directly:
  driving_video_url        -> driving_video.mp4   (high-bitrate raw Kling output, runtime driver)
  preview_video_url        -> preview_stream.mp4  (~5 Mbps, what the app plays)
  preview_video_url_orig   -> driving_video.mp4
  original_driving_video_url -> raw_source.mp4

After the doc write, the seed generates the first-frame poster (S81).

Starts as DRAFT — flip to published via `scripts/set_template_status.py`.

Re-running overwrites the Speed doc.

Usage:
    .venv/bin/python scripts/seed_speed_template.py
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
log = logging.getLogger("seed_speed_template")


TEMPLATE_ID = "viral-dances-speed"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

_BASE = "https://assets.speech-2-video.ai/viral-dances/speed"

SPEED_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "tiktok_dances",
    "title": "Speed",
    "description": "Late-night highway moves. 🛣️🌙",
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
    written = upsert_template(TEMPLATE_ID, SPEED_FIXTURE)
    log.info(
        "wrote: pipeline_class=%s status=%s credit_cost=%s use_nbp_regen=%s audio_enabled=%s",
        written.get("pipeline_class"),
        written.get("published_status"),
        written.get("credit_cost"),
        written.get("use_nbp_regen"),
        written.get("audio_enabled"),
    )

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
