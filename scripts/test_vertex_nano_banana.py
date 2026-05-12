"""Smoke test for Vertex AI Nano Banana Pro — T2I + Edit (AIV-11).

T2I always runs. Edit runs only when --selfie and --scene are both provided.

Usage:
    .venv/bin/python scripts/test_vertex_nano_banana.py
    .venv/bin/python scripts/test_vertex_nano_banana.py --selfie /path/to/selfie.jpg --scene /path/to/scene.jpg
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.clients.vertex_ai_client import VertexAIClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfie", help="Path to selfie image (for Edit smoke)")
    ap.add_argument("--scene", help="Path to scene image (for Edit smoke)")
    ap.add_argument(
        "--prompt-t2i",
        default="A red panda eating bamboo in a misty forest, photorealistic, soft morning light",
    )
    ap.add_argument(
        "--prompt-edit",
        default=(
            "Place the person from the first image into the scene from the second image. "
            "Photorealistic. Preserve the person's face and clothing. "
            "Match the lighting and color tone of the scene."
        ),
    )
    args = ap.parse_args()

    client = VertexAIClient()

    print("\n=== T2I ===")
    r = client.generate_image_nano_banana(prompt=args.prompt_t2i)
    if not r.get("success"):
        print(f"FAIL  T2I  error={r.get('error')}")
        return 1
    print(f"PASS  T2I   model={r['model']}  saved={r['local_path']}  mime={r['mime_type']}")

    if args.selfie and args.scene:
        print("\n=== Edit ===")
        r = client.edit_image_nano_banana(
            prompt=args.prompt_edit,
            image_paths=[args.selfie, args.scene],
        )
        if not r.get("success"):
            print(f"FAIL  Edit  error={r.get('error')}")
            return 1
        print(f"PASS  Edit  model={r['model']}  saved={r['local_path']}  mime={r['mime_type']}")
    else:
        print("\nSKIP  Edit  (pass --selfie and --scene to exercise Edit mode)")

    print("\nDone. Open the saved file(s) to inspect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
