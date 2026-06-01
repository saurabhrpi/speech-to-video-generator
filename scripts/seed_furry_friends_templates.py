"""Seed the Firestore registry with the Furry Friends category (S89).

NEW CATEGORY — `furry_friends` (renders "Furry Friends"; prettyCategory title-cases
cleanly, no CATEGORY_LABEL_OVERRIDES entry needed). Lands LAST on the home grid:
category row order = first-appearance in doc-ID-sorted order, and the earliest
furry doc-id (`viral-dances-cool-cat`) sorts after girl_dances' anchor
(`viral-dances-buttons`), with no unseen category appearing after it.

WHAT'S DIFFERENT FROM A NORMAL DANCE TEMPLATE
- Input is the user's PET photo, not a selfie. Runtime regen uses the animal core
  (`subject_type="animal"` → VideoService._GENERIC_NBP_REGEN_PROMPT_ANIMAL): no
  human reference, preserves the pet's identity, re-poses it standing upright so
  Kling Motion Control's (human) dance maps onto it. Backend change is S89.
- Kling Motion Control needs a HUMAN upper body in the driving video, so the
  driver is a reused human dance clip (Dance Flow / Soda Pop Moves) — referenced
  by URL, NOT copied (sharing a read-only CDN object has no perf cost; the only
  tradeoff is a dependency on those two templates' drivers staying in place).
- preview ≠ driver (preview = a generated PET dance; driver = the human clip).
  This inverts the catalog twin invariant, so `streaming_previews.py` skips
  animal templates (S89) — it must NOT re-derive these previews from the driver.
  `preview_video_url_orig` is set to the preview itself so a stray `--revert` is
  a no-op.

ASSET SHAPE (per template, under viral-dances/<slug>/):
  driving_video_url          -> SHARED human driver URL (referenced)
  preview_video_url          -> preview_stream.mp4  (~5 Mbps generated pet dance)
  preview_video_url_orig     -> preview_stream.mp4  (no-op revert; furry is exempt)
  original_driving_video_url -> SHARED human driver URL (revert target = the driver)
  thumbnail_url              -> filled by the seed (frame0 of preview_stream.mp4)

Starts as DRAFT. Flip to published with scripts/set_template_status.py AFTER the
S89 backend (animal regen core) is deployed — otherwise a runtime pet gen hits the
old human core and mangles the pet.

Usage:
    .venv/bin/python scripts/seed_furry_friends_templates.py
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
log = logging.getLogger("seed_furry_friends")

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

_ASSETS = "https://assets.speech-2-video.ai/viral-dances"
_DANCE_FLOW_DRIVER = f"{_ASSETS}/dance-flow/driving_video.mp4"
_SODA_POP_MOVES_DRIVER = f"{_ASSETS}/soda-pop-moves/driving_video.mp4"


def _fixture(slug: str, title: str, description: str, driver_url: str) -> dict:
    base = f"{_ASSETS}/{slug}"
    return {
        "pipeline_class": PIPELINE_MOTION_TRANSFER,
        "outcome": OUTCOME_ONTO_CHARACTER,
        "category": "furry_friends",
        "title": title,
        "description": description,
        "published_status": STATUS_DRAFT,
        "assets": {
            "driving_video_url": driver_url,
            "preview_video_url": f"{base}/preview_stream.mp4",
            "preview_video_url_orig": f"{base}/preview_stream.mp4",
            "original_driving_video_url": driver_url,
            "scene_image_url": None,
            "thumbnail_url": None,  # filled by generate_thumbnail below
        },
        "model": "kling-2.6-motion-control-image",
        "credit_cost": 500,
        "prompt_template": GENERIC_KLING_PROMPT,
        "use_nbp_regen": True,
        "nbp_framing_hint": "Composition: full body standing pose, head to paws.",
        "subject_type": "animal",
        "audio_enabled": True,
        "is_hero": False,
        "hero_order": None,
    }


# slugs chosen so the earliest (cool-cat) sorts after girl_dances' anchor
# (buttons) → furry_friends row lands last on the home grid.
FIXTURES = {
    "viral-dances-top-dog": _fixture(
        "top-dog", "Top Dog", "Your pup owns the dance floor. 🐶", _SODA_POP_MOVES_DRIVER,
    ),
    "viral-dances-puppy-love": _fixture(
        "puppy-love", "Puppy Love", "Puppy's got moves. 🐾", _DANCE_FLOW_DRIVER,
    ),
    "viral-dances-cool-cat": _fixture(
        "cool-cat", "Cool Cat", "One cool cat. 😼", _DANCE_FLOW_DRIVER,
    ),
}


def main() -> None:
    for template_id, fixture in FIXTURES.items():
        log.info("seeding %s", template_id)
        written = upsert_template(template_id, fixture)
        log.info(
            "  wrote: title=%s category=%s subject_type=%s credit_cost=%s driver=%s",
            written.get("title"), written.get("category"), written.get("subject_type"),
            written.get("credit_cost"),
            (written.get("assets") or {}).get("driving_video_url", "").rsplit("/", 2)[-2:],
        )
        try:
            log.info("  thumbnail: %s", generate_thumbnail(written, force=True))
        except Exception as e:  # noqa: BLE001 — poster best-effort; doc already written
            log.warning("  thumbnail generation failed (backfill later): %s", e)

        fetched = get_template(template_id)
        a = fetched.get("assets") or {}
        log.info(
            "  read back: preview=%s thumbnail=%s",
            (a.get("preview_video_url") or "").rsplit("/", 1)[-1],
            (a.get("thumbnail_url") or "").rsplit("/", 1)[-1] or None,
        )


if __name__ == "__main__":
    main()
