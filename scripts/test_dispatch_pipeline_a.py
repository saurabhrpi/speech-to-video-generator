"""Smoke test for AIV-14 dispatcher — Pipeline A (motion-transfer) end-to-end.

Loads a published template from Firestore, presigns a selfie key from R2,
calls Kling Motion Control image mode, returns the resulting mp4 URL.

`--driving-video-url` is a TEST-ONLY override — splices a different driving
video into the loaded template via in-process monkey-patch on the registry.
The Firestore doc itself is unmodified. Use when the seeded template has a
placeholder URL you want to bypass for end-to-end smoke testing.

Pipeline B smoke is deferred until a Pipeline B template is seeded in Firestore.

Usage:
    .venv/bin/python scripts/test_dispatch_pipeline_a.py \\
        --template viral-dances-bombale \\
        --selfie-key me.jpg \\
        --driving-video-url https://assets.speech-2-video.ai/dance.mp4
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.services.video_service import VideoService  # noqa: E402
from src.speech_to_video.utils import template_registry  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _on_progress(**kwargs):
    print(f"  [progress] {kwargs}")


def _patch_template_registry(driving_video_url: str | None):
    """Splice a driving_video_url override into the loaded template (test only)."""
    if not driving_video_url:
        return
    orig = template_registry.get_template

    def patched(template_id: str):
        t = orig(template_id)
        t = dict(t)
        t["assets"] = dict(t.get("assets") or {})
        t["assets"]["driving_video_url"] = driving_video_url
        return t

    template_registry.get_template = patched
    print(f"  [test override] driving_video_url -> {driving_video_url!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="template_id (e.g. viral-dances-bombale)")
    ap.add_argument("--selfie-key", required=True, help="R2 object key in selfies bucket")
    ap.add_argument(
        "--driving-video-url",
        help="TEST OVERRIDE: bypass the template's seeded driving_video_url for this run. "
        "Firestore doc is NOT modified.",
    )
    args = ap.parse_args()

    _patch_template_registry(args.driving_video_url)

    svc = VideoService()
    print(f"Dispatching template={args.template!r} selfie_key={args.selfie_key!r}")
    result = svc.generate_template_video(
        template_id=args.template,
        selfie_key=args.selfie_key,
        on_progress=_on_progress,
    )

    print("\n=== RESULT ===")
    if result.get("success"):
        print(f"PASS  pipeline={result.get('pipeline')}  task_id={result.get('task_id')}")
        print(f"      duration={result.get('duration')}s")
        print(f"      video_url={result.get('video_url')}")
        if result.get("intermediate_image_key"):
            print(f"      intermediate composite key={result['intermediate_image_key']}")
        return 0

    print(f"FAIL  phase={result.get('phase')}")
    print(f"      error={result.get('error')}")
    if result.get("task_id"):
        print(f"      task_id={result.get('task_id')}")
    if result.get("intermediate_image_key"):
        print(f"      intermediate composite key (recoverable)={result['intermediate_image_key']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
