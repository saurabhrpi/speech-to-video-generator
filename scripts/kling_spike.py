"""S58 Kling Motion Control spike.

Toggles between Outcome-2 (image mode) and Outcome-1 (video mode) via the
KLING_ORIENTATION env var. Same selfie + dance video as S57 Pollo / Swaptok.
"""
import base64
import logging
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.clients.kling_motion_client import KlingMotionClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ORIENTATION = os.environ.get("KLING_ORIENTATION", "image")
assert ORIENTATION in {"image", "video"}, "KLING_ORIENTATION must be 'image' or 'video'"
OUT_TAG = "Image" if ORIENTATION == "image" else "Video"

IMAGE_PATH = ROOT / "debug" / "Me.jpg"
VIDEO_URL = "https://files.catbox.moe/xwiktk.mp4"
OUT_PATH = ROOT / "docs" / "research" / f"Kling_MotionControl_{OUT_TAG}_Output.mp4"

image_b64 = base64.b64encode(IMAGE_PATH.read_bytes()).decode("ascii")
print(f"Image base64 length: {len(image_b64)} (raw bytes: {IMAGE_PATH.stat().st_size})")
print(f"Video URL: {VIDEO_URL}")

client = KlingMotionClient()
result = client.generate_and_poll(
    image_url=image_b64,
    video_url=VIDEO_URL,
    character_orientation=ORIENTATION,
    mode="pro",
    model_name="kling-v2-6",
    keep_original_sound="yes",
    max_wait=600,
    poll_interval=10,
)

print("\n=== RESULT ===")
for k, v in result.items():
    if k == "video_url":
        print(f"{k}: {v}")
    elif isinstance(v, (dict, list)):
        print(f"{k}: <{type(v).__name__}>")
    else:
        print(f"{k}: {v}")

if result.get("success"):
    url = result["video_url"]
    print(f"\nDownloading {url} -> {OUT_PATH}")
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    print(f"Saved: {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
else:
    print("\nSpike failed — see error above. Full result:")
    import json
    print(json.dumps(result, default=str, indent=2)[:2000])
