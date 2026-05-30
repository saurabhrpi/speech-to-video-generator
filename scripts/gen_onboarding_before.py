"""Generate the onboarding "Before" selfie image for a dance template.

For the V2 onboarding screen (Onboarding.png reference): each featured slide
shows the dance VIDEO (the "after") plus a small circular "Before" still. The
"Before" is an NBP-regenerated *solo selfie* derived from the video's first
frame — so it reads like a casual photo the user uploaded, not a dance frame.

Pipeline (per slug): driving_video.mp4 frame 0  ->  NBP regen (generic
solo-selfie prompt)  ->  mobile/assets/onboarding/<slug>_before.jpg (bundled).

The prompt CORE is generic across all subjects (no overfitting — see
Memory/feedback_no_overfit_prompts.md); it is regen-framed, not preserve-framed
(Memory/feedback_regen_vs_preserve_prompts.md), because we are changing the
scene/pose wholesale, not tweaking it.

Usage:
    .venv/bin/python scripts/gen_onboarding_before.py --slug bombale
    .venv/bin/python scripts/gen_onboarding_before.py --slug gangsta
    .venv/bin/python scripts/gen_onboarding_before.py --slug mapopo
"""
from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

R2_BASE = "https://assets.speech-2-video.ai/viral-dances"
OUT_DIR = ROOT / "mobile" / "assets" / "onboarding"

# Generic, regen-framed. Works for any subject; specifics (who) come from the
# input frame, never from this string.
PROMPT = (
    "Regenerate this image as a clean, casual portrait photo of the same person — "
    "JUST the person. Absolutely NO phone, smartphone, camera, mirror, device, or "
    "reflection anywhere in the frame, and no hand raised as if holding a device. "
    "Head-and-shoulders to upper-body framing, facing the camera with a relaxed, "
    "natural, friendly expression and arms in a relaxed, natural position. Place "
    "them against a simple, plain, softly-lit neutral background — NOT the original "
    "scene or stage. Natural everyday lighting. Preserve the person's identity, "
    "face, hairstyle, skin tone, and general appearance and clothing style. Remove "
    "any motion blur or performance pose. No text, no graphics, no watermarks."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="R2 slug, e.g. bombale / gangsta / mapopo")
    args = ap.parse_args()
    slug = args.slug

    from src.speech_to_video.utils.video import extract_first_frame
    from src.speech_to_video.clients.gemini_client import GeminiClient

    video_url = f"{R2_BASE}/{slug}/driving_video.mp4"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{slug}_before.jpg"

    # 1) frame 0
    with tempfile.TemporaryDirectory() as td:
        frame_png = str(Path(td) / "frame0.png")
        log.info("extracting frame 0 from %s", video_url)
        extract_first_frame(video_url, frame_png)
        frame_bytes = Path(frame_png).read_bytes()
        log.info("frame0 bytes=%d", len(frame_bytes))

        # 2) NBP regen -> solo selfie
        client = GeminiClient()
        res = client.regen_image(frame_bytes, "image/png", PROMPT)
        if not res.get("success"):
            log.error("NBP failed: %s", res.get("error"))
            return 1
        img_bytes, mime = res["image_bytes"], res.get("mime", "image/png")
        log.info("NBP ok mime=%s bytes=%d", mime, len(img_bytes))

    # 3) normalize to JPG (smaller bundle, RGB) via Pillow; fallback = raw bytes
    try:
        from PIL import Image

        im = Image.open(BytesIO(img_bytes)).convert("RGB")
        im.save(out_path, "JPEG", quality=90)
        log.info("saved %s (%dx%d)", out_path, im.width, im.height)
    except Exception as e:  # pragma: no cover
        log.warning("Pillow normalize failed (%s); writing raw bytes", e)
        out_path.write_bytes(img_bytes)
        log.info("saved %s (raw)", out_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
