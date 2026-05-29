"""Seed the Firestore template registry with the Copacabana fixture (S83).

Thirteenth template of the tiktok_dances category. Sister to
scripts/seed_seteadora_template.py / the canonical
scripts/seed_buttons_template.py.

Category: tiktok_dances (mobile label override -> "TikTok Dances").

Preview note (S83): Pattern B holistic regen — DIFFERENT Latino man, dark
hair, athletic, in an UPSCALE JAZZ / COCKTAIL LOUNGE (low-key warm light,
tufted leather, brass). Source was a wood-paneled gentleman's-club / pub
register; the regen relocated him to a cocktail bar with DISTINCT composition.

Lateral-room re-roll (S83): the first NBP edit had the booths flanking the
subject too closely (no lateral dance room). Pattern A re-edit pushed the
booths farther out to the frame edges, leaving generous open wooden floor on
both sides for the source dance's arm-wave + Latin-stance choreography.

Wardrobe = fitted black silk shirt + slim gray trousers + leather dress shoes
(source = white long-sleeve crew tee + dark-wash jeans). Source trimmed to
~9.6s from a 0.5s start.

AUDIO-LEAD FIX + TAIL-TRIM (S83): the pro Kling output had the intrinsic
~0.5s audio lead. The corrected master is +0.5s itsoffset + head-trim 0.5s +
TAIL-trim 0.5s (user direction — clean up the tail of the Kling output).
BOTH the driver AND the preview are encoded from that same corrected master
(8.60s) at two bitrates. See
Memory/feedback_kling_audio_lead_and_preview_propagation.md.

Assets land in the S77 migrated shape directly:
  driving_video_url        -> driving_video.mp4   (high-bitrate CORRECTED twin of the preview, runtime driver)
  preview_video_url        -> preview_stream.mp4  (~5 Mbps CORRECTED, what the app plays)
  preview_video_url_orig   -> driving_video.mp4
  original_driving_video_url -> raw_source.mp4

After the doc write, the seed generates the first-frame poster (S81).

Starts as DRAFT — flip to published via `scripts/set_template_status.py`.

Re-running overwrites the Copacabana doc.

Usage:
    .venv/bin/python scripts/seed_copacabana_template.py
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
log = logging.getLogger("seed_copacabana_template")


TEMPLATE_ID = "viral-dances-copacabana"

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

_BASE = "https://assets.speech-2-video.ai/viral-dances/copacabana"

COPACABANA_FIXTURE = {
    "pipeline_class": PIPELINE_MOTION_TRANSFER,
    "outcome": OUTCOME_ONTO_CHARACTER,
    "category": "tiktok_dances",
    "title": "Copacabana",
    "description": "Music and passion, always in fashion. 🥃✨",
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
    written = upsert_template(TEMPLATE_ID, COPACABANA_FIXTURE)
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
