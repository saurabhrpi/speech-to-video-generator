"""Smoke test for Veo via Google AI Studio direct.

S65 spike: T2V smoke for one launch template (default = Bombale) to test
whether Veo can capture a TikTok-trend dance from a prose description (per
AIV-17 production plan).

Reads NBP_API_Key from .env. Submits a long-running job, polls every 10s,
downloads the resulting video to /tmp.

Cost (per the AI Studio pricing page, May 2026):
    veo-3.1-fast-generate-preview at 1080p × 8s = $0.96
    veo-3.1-generate-preview      at 1080p × 8s = $3.20

Usage:
    .venv/bin/python scripts/test_aistudio_veo.py
    .venv/bin/python scripts/test_aistudio_veo.py --model veo-3.1-generate-preview
    .venv/bin/python scripts/test_aistudio_veo.py --prompt "...custom prompt..."
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

DEFAULT_MODEL = "veo-3.1-fast-generate-preview"

DEFAULT_PROMPT = (
    "A solo young woman dances confidently in a dark photo studio. "
    "She wears a black sports bra, black leggings, white sneakers. "
    "Studio gel lighting: deep blue from the left, warm red-pink from the right, "
    "creating a purple rim light on her shoulders and a soft pink glow on the background wall. "
    "Full body in frame, portrait orientation, camera locked off at chest height.\n\n"
    "She is performing the Bombale dance — a viral Indonesian/TikTok dance with "
    "energetic, explosive hip and arm motion. Her motion: relaxed stance with feet "
    "wider than shoulders, hips swaying side to side on the beat, arms swinging "
    "alternately across her body in rhythm, occasional shoulder roll and slight knee dip. "
    "Smooth, confident, untouchable energy. Cinematic, photorealistic, 24fps."
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _api_key() -> str:
    key = os.environ.get("NBP_API_Key") or os.environ.get("NBP_API_KEY")
    if not key:
        print("FAIL  NBP_API_Key not found in .env", file=sys.stderr)
        sys.exit(2)
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--duration", type=int, default=8)
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--aspect-ratio", default="9:16", help="9:16 portrait, 16:9 landscape")
    ap.add_argument("--out-dir", default="/tmp")
    ap.add_argument("--poll-secs", type=int, default=10)
    ap.add_argument("--max-secs", type=int, default=600, help="Give up after this many seconds")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"aistudio_veo_{uuid.uuid4().hex[:8]}.mp4"

    log.info("model=%s  duration=%ds  resolution=%s  aspect=%s",
             args.model, args.duration, args.resolution, args.aspect_ratio)
    log.info("prompt:\n%s", args.prompt)

    client = genai.Client(api_key=_api_key())

    cfg = types.GenerateVideosConfig(
        duration_seconds=args.duration,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        number_of_videos=1,
        generate_audio=False,  # Kling passes any audio through to the output; we want silent.
    )

    t0 = time.time()
    log.info("submitting Veo job...")
    try:
        op = client.models.generate_videos(
            model=args.model,
            prompt=args.prompt,
            config=cfg,
        )
    except Exception as e:
        print(f"FAIL  submit  {type(e).__name__}: {e}")
        return 1

    log.info("submitted; op=%s — polling every %ds (max %ds)", op.name, args.poll_secs, args.max_secs)

    while not op.done:
        if time.time() - t0 > args.max_secs:
            print(f"FAIL  poll  timeout after {args.max_secs}s")
            return 1
        time.sleep(args.poll_secs)
        try:
            op = client.operations.get(op)
        except Exception as e:
            print(f"FAIL  poll  {type(e).__name__}: {e}")
            return 1
        log.info("...still running, elapsed=%.0fs", time.time() - t0)

    elapsed = time.time() - t0
    log.info("op done in %.0fs", elapsed)

    if op.error:
        print(f"FAIL  op  error={op.error}")
        return 1

    # Extract video — response shape: response.generated_videos[].video
    resp = op.response
    if not resp or not getattr(resp, "generated_videos", None):
        print(f"FAIL  no generated_videos in op.response: {str(resp)[:400]}")
        return 1
    video = resp.generated_videos[0].video
    log.info("video meta: %s", video)

    # Download to local file
    try:
        client.files.download(file=video)
        video.save(str(out_path))
    except Exception as e:
        print(f"FAIL  download  {type(e).__name__}: {e}")
        return 1

    size = out_path.stat().st_size if out_path.exists() else 0
    print(f"PASS  Veo  model={args.model}  saved={out_path}  bytes={size}  elapsed={elapsed:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
