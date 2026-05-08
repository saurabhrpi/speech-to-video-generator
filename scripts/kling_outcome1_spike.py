"""S58 Kling-via-input-shaping spike: Outcome 1 (user in template's scene).

Pipeline:
  1. AIMLAPI Nano Banana Pro Edit: identity-transfer user into the dance video's
     first frame (preserves video's pose, clothing, background; transforms face,
     skin tone, hair, exposed body parts to match user identity).
  2. Feed the swapped frame as `image_url` + original dance video as `video_url`
     to Kling Motion Control `image` mode.

Two-stage flow controlled by KLING_RUN_STEP env var:
  - "swap_only" (default): run Nano Banana only, print swapped URL, stop.
    Lets us iterate the prompt without burning Kling credits.
  - "full": run swap + Kling.
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
SWAPPED_URL_OVERRIDE = os.environ.get("SWAPPED_URL")  # skip step 1 if set

DANCE_VIDEO_URL = "https://files.catbox.moe/xwiktk.mp4"
FIRST_FRAME_URL = "https://files.catbox.moe/1p1hry.jpg"
USER_PHOTO_URL = "https://files.catbox.moe/gt61hw.jpg"
ORIENTATION = os.environ.get("KLING_ORIENTATION", "video")
assert ORIENTATION in {"image", "video"}
OUT_PATH = ROOT / "docs" / "research" / f"Kling_Outcome1_Regen_{ORIENTATION.capitalize()}Mode_Output.mp4"

# v4 prompt — holistic character regeneration in scene (S58, user proposal).
# v1/v3 were "preserve everything except face" — produced paste-in face/lighting.
# v4 reframes the task: regenerate the SECOND image's person (full identity
# AND clothing, including imagined body parts not visible in selfie) into the
# FIRST image's pose, dimensions, scene, and lighting. Clothing follows the
# user, not the dancer. Lower body / shoes / etc. are imagined to fit the
# user's style.
REGEN_PROMPT = (
    "Holistic character regeneration. Generate a single coherent photograph "
    "by combining elements from the two reference images as follows. "
    "\n\n"
    "FROM THE FIRST IMAGE (the scene template), preserve exactly: the pose, "
    "body position and posture, body dimensions, framing, camera angle, "
    "scene, background, and lighting. The character in the output should "
    "occupy the same area of the frame, in the same pose, lit the same way."
    "\n\n"
    "FROM THE SECOND IMAGE (the identity source), take everything about the "
    "person: face, facial features, facial structure, hair, hair style, skin "
    "tone (apply consistently across all visible skin — face, neck, arms, "
    "hands, legs), body type and proportions, AND the clothing they are "
    "wearing in the second image (e.g. their shirt or sweater). Any "
    "accessories the second image's person wears (eyeglasses, religious head "
    "covering, jewelry) should also appear on the regenerated character. "
    "\n\n"
    "IMAGINE NATURALLY for body parts not visible in the second image: e.g. "
    "if the second image is a chest-up portrait but the first image's pose "
    "shows a full body, imagine the lower body (legs, feet, pants/trousers, "
    "shoes) in a style consistent with the second image's existing visible "
    "clothing — NOT matching the first image's character's clothing. The "
    "imagined lower-body clothing should be casual and consistent with what "
    "the user appears to wear in their selfie. "
    "\n\n"
    "DO NOT preserve from the first image: the original character's identity, "
    "face, hair, skin tone, body type, OR clothing. Those are all replaced. "
    "The first image is ONLY a pose / scene / lighting reference. "
    "\n\n"
    "DO NOT do a localized face swap. Regenerate the entire character "
    "holistically so the lighting, skin tone, clothing, and pose all look "
    "natural and integrated within the first image's scene. The result must "
    "look like a single believable photograph, not a paste-in or composite."
)

# Step 1: holistic regen via Nano Banana Pro Edit (v4 prompt) — skipped if SWAPPED_URL is set
if SWAPPED_URL_OVERRIDE:
    swapped_url = SWAPPED_URL_OVERRIDE
    print("=== Step 1 SKIPPED (using SWAPPED_URL override) ===")
    print(f">>> SWAPPED FRAME URL: {swapped_url}")
else:
    aiml = AIMLAPIClient()
    print("=== Step 1: AIMLAPI Nano Banana Pro Edit (holistic regen, v4 prompt) ===")
    edit_result = aiml.generate_image(
        prompt=REGEN_PROMPT,
        image_urls=[FIRST_FRAME_URL, USER_PHOTO_URL],
        aspect_ratio="16:9",
        resolution="1K",
    )
    print(f"AIMLAPI result success: {edit_result.get('success')}")
    if not edit_result.get("success"):
        print(f"AIMLAPI failed: {edit_result.get('error')}")
        sys.exit(1)

    swapped_url = edit_result["images"][0]
    print(f"\n>>> SWAPPED FRAME URL: {swapped_url}")

if RUN_STEP == "swap_only":
    print("\nStopping here (KLING_RUN_STEP=swap_only).")
    print("Inspect the URL above. Re-run with KLING_RUN_STEP=full to continue to Kling.")
    sys.exit(0)

# Step 2: Kling Motion Control
print(f"\n=== Step 2: Kling Motion Control ({ORIENTATION} orientation, pro) on regen frame ===")
kling = KlingMotionClient()
kling_result = kling.generate_and_poll(
    image_url=swapped_url,
    video_url=DANCE_VIDEO_URL,
    character_orientation=ORIENTATION,
    mode="pro",
    model_name="kling-v2-6",
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
