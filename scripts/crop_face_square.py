"""Crop a portrait to a face/shoulders square so it reads well in the onboarding
circular "Before" thumbnail (which uses cover-crop, centering on the middle).

Square side = min(width, side_frac*height); vertically anchored so a typical
face center (~anchor*height) sits near the square's middle. Tune --anchor /
--side-frac per image if framing is off; eyeball the result.

Usage:
    .venv/bin/python scripts/crop_face_square.py --image PATH [--anchor 0.32] [--side-frac 0.62] [--out PATH]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--anchor", type=float, default=0.32, help="face center as fraction of height")
    ap.add_argument("--side-frac", type=float, default=0.62, help="square side as fraction of height (clamped to width)")
    ap.add_argument("--out", default=None, help="default: overwrite --image")
    args = ap.parse_args()

    src = Path(args.image)
    out = Path(args.out) if args.out else src
    im = Image.open(src).convert("RGB")
    W, H = im.size
    side = int(min(W, args.side_frac * H))
    cy = int(args.anchor * H)
    top = max(0, min(H - side, cy - side // 2))
    left = max(0, (W - side) // 2)
    im.crop((left, top, left + side, top + side)).save(out, "JPEG", quality=90)
    print(f"cropped {src.name}: {W}x{H} -> {side}x{side} (top={top} left={left}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
