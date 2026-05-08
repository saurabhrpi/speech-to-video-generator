"""S58 Outcome-1 spike v2: body-extension pipeline.

Replaces the v1 face-swap-on-video-frame approach (which hit a lighting-
integration ceiling). New approach:

  1. Nano Banana Pro Edit: extend the user's bust-shot photo to a full-body
     photo (neutral standing pose, same identity, natural clothing/background
     extension). Gives Kling framing-compatible body data.
  2. Kling Motion Control `video` orientation: re-render the user (full-body)
     into the dance video's scene + lighting + framing, doing the dance.

Two-stage flow controlled by KLING_RUN_STEP env var:
  - "swap_only" (default): Nano Banana only. Inspect URL, iterate prompt cheaply.
  - "full": extend + Kling.

User-confirmed inputs (catbox-hosted):
  - User selfie:                https://files.catbox.moe/gt61hw.jpg
  - Dance video (10s trim):     https://files.catbox.moe/xwiktk.mp4
"""
import logging
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.clients.aimlapi_client import AIMLAPIClient
from src.speech_to_video.clients.kling_motion_client import KlingMotionClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RUN_STEP = os.environ.get("KLING_RUN_STEP", "swap_only")
assert RUN_STEP in {"swap_only", "full"}
ORIENTATION = os.environ.get("KLING_ORIENTATION", "video")
assert ORIENTATION in {"image", "video"}
EXTENDED_URL_OVERRIDE = os.environ.get("EXTENDED_URL")  # skip step 1 if set

USER_PHOTO_URL = "https://files.catbox.moe/gt61hw.jpg"
DANCE_VIDEO_URL = "https://files.catbox.moe/xwiktk.mp4"
OUT_TAG = f"BodyExtend_{ORIENTATION.capitalize()}Mode"
OUT_PATH = ROOT / "docs" / "research" / f"Kling_Outcome1_{OUT_TAG}_Output.mp4"

BODY_EXTEND_PROMPT = (
    "Take the person in this image (currently shown from the chest up) and "
    "generate a full-body portrait of the same person. "
    "\n\n"
    "PRESERVE EXACTLY: the person's face, hair, skin tone, facial structure, "
    "expression, glasses or accessories they wear, and the existing visible "
    "clothing (sweater/shirt). "
    "\n\n"
    "GENERATE NATURALLY (use realistic imagination): the rest of their torso, "
    "arms (relaxed at their sides in a natural standing pose), hands, legs, "
    "and feet. Body proportions must match what is implied by the visible "
    "head and shoulders. Skin tone on hands and any visible skin must match "
    "the face. Add believable casual clothing for the lower body (e.g. jeans "
    "or trousers and shoes) consistent with the visible upper-body clothing. "
    "Extend the existing background naturally so the full-body shot looks "
    "like a single coherent photograph. "
    "\n\n"
    "POSE: a natural standing pose, facing the camera straight-on, arms "
    "relaxed at sides, both feet visible on the ground. NOT dancing, NOT "
    "any specific action — just standing. "
    "\n\n"
    "OUTPUT: a single full-body portrait photo of this exact person, looking "
    "like a believable real photograph (not an AI montage)."
)

KLING_PROMPT = (
    "A realistic video of the person from the reference image performing the "
    "exact same motion, timing, gestures, and facial expressions as the "
    "motion reference video. Keep the scene composition, camera angle, "
    "lighting, and background similar to the reference video. Stable face, "
    "natural hands, no morphing."
)

# Step 1: extend user photo to full-body (skipped if EXTENDED_URL is provided)
if EXTENDED_URL_OVERRIDE:
    extended_url = EXTENDED_URL_OVERRIDE
    print(f"=== Step 1 SKIPPED (using EXTENDED_URL override) ===")
    print(f">>> EXTENDED FULL-BODY URL: {extended_url}")
else:
    aiml = AIMLAPIClient()
    print("=== Step 1: AIMLAPI Nano Banana Pro Edit (body extension) ===")
    edit_result = aiml.generate_image(
        prompt=BODY_EXTEND_PROMPT,
        image_urls=[USER_PHOTO_URL],
        aspect_ratio="9:16",
        resolution="1K",
    )
    print(f"AIMLAPI result success: {edit_result.get('success')}")
    if not edit_result.get("success"):
        print(f"AIMLAPI failed: {edit_result.get('error')}")
        sys.exit(1)

    extended_url = edit_result["images"][0]
    print(f"\n>>> EXTENDED FULL-BODY URL: {extended_url}")

if RUN_STEP == "swap_only":
    print("\nStopping here (KLING_RUN_STEP=swap_only).")
    print("Inspect the URL above. Re-run with KLING_RUN_STEP=full to continue to Kling.")
    sys.exit(0)

# Step 2: Kling Motion Control, video orientation, with prompt
print(f"\n=== Step 2: Kling 2.6 Motion Control ({ORIENTATION} orientation, pro) ===")
kling = KlingMotionClient()
kling_result = kling.generate_and_poll(
    image_url=extended_url,
    video_url=DANCE_VIDEO_URL,
    character_orientation=ORIENTATION,
    mode="pro",
    model_name="kling-v2-6",
    prompt=KLING_PROMPT,
    keep_original_sound="yes",
    max_wait=600,
    poll_interval=10,
)

print("\n=== KLING RESULT ===")
for k, v in kling_result.items():
    if k == "video_url":
        print(f"{k}: {v}")
    elif isinstance(v, (dict, list)):
        print(f"{k}: <{type(v).__name__}>")
    else:
        print(f"{k}: {v}")

if kling_result.get("success"):
    url = kling_result["video_url"]
    print(f"\nDownloading -> {OUT_PATH}")
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    print(f"Saved: {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
else:
    print("\nSpike failed at Kling step.")
    import json
    print(json.dumps(kling_result, default=str, indent=2)[:2000])
