"""Seed the Firestore template registry with the Got 2 Luv U fixture (S83).

Fifteenth template of the tiktok_dances category. Sister to
scripts/seed_speed_template.py / the canonical scripts/seed_buttons_template.py.

Category: tiktok_dances (mobile label override -> "TikTok Dances").

Preview note (S83): Pattern B holistic regen — DIFFERENT light-skinned mixed-
race woman with warm-tone wavy hair, slim build, in a cozy real LIVING ROOM
with natural indoor lighting (NOT the theatrical photo-studio v1 with the
overhead spotlight — user S83 redirect). Wardrobe = peach knit sweater +
cream wide-leg jeans (source = cream sweater + mid-wash blue jeans). Source
was 15.21s HEVC, no trim — codec-normalized only (user direction).

Lateral-room re-roll (S83): the first v2 indoor edit had a beige sofa + arc
floor lamp + plants within arm's reach of the subject. Pattern A re-edit
(v3) pushed all furniture far back / to the corners of the room, leaving
generous open hardwood floor on both sides for the source's hip and arm
gestures. See Memory/reference_kling_mc_aspect_inherits_nbp.md for the
lateral-room spatial-allowance lesson (S83 finding: cramped framing causes
face distortion in Kling output, not just cramped dance).

AUDIO-LEAD: not applied this template — user verified the v3 roll's audio
was already in sync (the Kling MC v2.6+pro+video audio-lead is per-gen-
variable per Memory/feedback_kling_audio_lead_and_preview_propagation.md).
Driver = raw Kling output (no re-encode); preview = ~5 Mbps re-encode of the
same source.

Assets land in the S77 migrated shape directly:
  driving_video_url        -> driving_video.mp4   (high-bitrate raw Kling output, runtime driver)
  preview_video_url        -> preview_stream.mp4  (~5 Mbps, what the app plays)
  preview_video_url_orig   -> driving_video.mp4
  original_driving_video_url -> raw_source.mp4

After the doc write, the seed generates the first-frame poster (S81).

Starts as DRAFT — flip to published via `scripts/set_template_status.py`.

Re-running overwrites the Got 2 Luv U doc.

Usage:
    .venv/bin/python scripts/seed_got_2_luv_u_template.py
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
log = logging.getLogger("seed_got_2_luv_u_template")


TEMPLATE_ID = "viral-dances-got-2-luv-u"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

_BASE = "https://assets.speech-2-video.ai/viral-dances/got-2-luv-u"

GOT_2_LUV_U_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "tiktok_dances",
    "title": "Got 2 Luv U",
    "description": "Living-room vibes. 🛋️💕",
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
    written = upsert_template(TEMPLATE_ID, GOT_2_LUV_U_FIXTURE)
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
