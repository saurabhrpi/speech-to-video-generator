"""Generic in-place NBP (Nano Banana Pro) edit of a local image.

Usage:
    .venv/bin/python scripts/nbp_edit_image.py --image PATH --prompt "..." [--out PATH]
"""
from __future__ import annotations

import argparse
import logging
import sys
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default=None, help="default: overwrite --image")
    args = ap.parse_args()

    from src.speech_to_video.clients.gemini_client import GeminiClient

    src = Path(args.image)
    out = Path(args.out) if args.out else src
    data = src.read_bytes()
    ext = src.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")

    res = GeminiClient().regen_image(data, mime, args.prompt)
    if not res.get("success"):
        log.error("NBP failed: %s", res.get("error"))
        return 1

    img = res["image_bytes"]
    try:
        from PIL import Image

        im = Image.open(BytesIO(img)).convert("RGB")
        im.save(out, "JPEG", quality=90)
        log.info("saved %s (%dx%d)", out, im.width, im.height)
    except Exception as e:  # pragma: no cover
        log.warning("Pillow normalize failed (%s); writing raw", e)
        out.write_bytes(img)
        log.info("saved %s (raw)", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
