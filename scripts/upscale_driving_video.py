"""Upscale a low-res driving video via Replicate Real-ESRGAN (S70).

Some TikTok downloader sites serve compressed 576×1024 versions of source
clips. Kling Motion Control degrades on low-res input (lost pose detail →
"jacket disappears", "dancer disoriented"). This script runs
lucataco/real-esrgan-video to upscale to FHD (1080×1920 portrait) before the
driving video is uploaded to R2.

Model: lucataco/real-esrgan-video (pinned version below)
  - video_path: input video (local file or URL)
  - resolution: FHD / 2k / 4k (default FHD)
  - model: RealESRGAN_x4plus (default, real-world) /
           RealESRGAN_x4plus_anime_6B / realesr-animevideov3

Usage:
    .venv/bin/python scripts/upscale_driving_video.py \
        --input https://assets.speech-2-video.ai/viral-dances/beat-it/driving_video.mp4 \
        --output "/Users/.../App Templates Prep/Beat_It_clip_fhd.mp4"

NOTE: --input must be a publicly fetchable URL, NOT a local file path. The
Replicate file-upload host (`/v1/files`) was unreachable from the model
worker during S70 testing — predictions failed in 3-5s with a misleading
"Cog: Got error trying to upload output files" error. Workaround: upload the
clip to R2 first (via `scripts/upload_template_assets.py`), then pass the
public URL here.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

import replicate  # noqa: E402

MODEL_VERSION = (
    "lucataco/real-esrgan-video:"
    "3e56ce4b57863bd03048b42bc09bdd4db20d427cca5fde9d8ae4dc60e1bb4775"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input",
        required=True,
        help="Publicly fetchable URL of the input .mp4 (NOT a local path — "
        "Replicate's file-upload host was unreachable from the model worker in S70). "
        "Upload to R2 via scripts/upload_template_assets.py first.",
    )
    ap.add_argument("--output", required=True, help="Local path for upscaled .mp4")
    ap.add_argument(
        "--resolution",
        default="FHD",
        choices=["FHD", "2k", "4k"],
        help="Target output resolution (default FHD = 1080p)",
    )
    ap.add_argument(
        "--model",
        default="RealESRGAN_x4plus",
        choices=[
            "RealESRGAN_x4plus",
            "RealESRGAN_x4plus_anime_6B",
            "realesr-animevideov3",
        ],
        help="Upscaling model (default RealESRGAN_x4plus, real-world content)",
    )
    args = ap.parse_args()

    if not args.input.lower().startswith(("http://", "https://")):
        print(f"FAIL  --input must be a URL (not a local path): {args.input}", file=sys.stderr)
        return 2
    if " " in args.input.rsplit("/", 1)[-1]:
        print(f"FAIL  URL filename must not contain spaces (model constraint): {args.input}", file=sys.stderr)
        return 2
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("FAIL  REPLICATE_API_TOKEN not set in .env", file=sys.stderr)
        return 2

    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    log.info("Replicate submit  model=%s  input=%s  resolution=%s  model=%s",
             MODEL_VERSION.split(":")[0], args.input, args.resolution, args.model)
    t0 = time.time()
    output = replicate.run(
        MODEL_VERSION,
        input={
            "video_path": args.input,
            "resolution": args.resolution,
            "model": args.model,
        },
    )
    elapsed = time.time() - t0
    log.info("Replicate complete  elapsed=%.1fs  output_type=%s", elapsed, type(output).__name__)

    # Output is a single FileOutput (or list with one). Normalize.
    if isinstance(output, list):
        if not output:
            print("FAIL  empty output list", file=sys.stderr)
            return 1
        file_obj = output[0]
    else:
        file_obj = output

    data = file_obj.read()
    out.write_bytes(data)

    print(f"PASS  upscale  elapsed={elapsed:.1f}s  size={len(data)//1024} KB")
    print(f"      saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
