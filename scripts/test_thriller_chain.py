"""V2 Pipeline A Thriller template — NBP-edit → Kling Motion Control chain (S72).

Sister to scripts/test_smooth_criminal_chain.py with two divergences for the
S72 spike:
  - model_name = "kling-v3-0" (Kling 3.0 Motion Control, S72 default bump)
  - character_orientation = "video" (15s driving clip; pose orientation from
    the driving video; output is still Outcome 2 per S58 — input image's
    background wins — but duration cap moves from 10s → 30s)
  - mode = "std" (720p) for cost

This is the first template to use the longer-form Pipeline A path. If the
output is coherent and faces stay consistent, this becomes the template's
production seed; if not, fall back to image-mode 10s.

Usage:
    .venv/bin/python scripts/test_thriller_chain.py
    .venv/bin/python scripts/test_thriller_chain.py --no-kling
    .venv/bin/python scripts/test_thriller_chain.py --edited-image ~/Downloads/thriller_edit_xxx.jpg
"""
from __future__ import annotations

import argparse
import logging
import mimetypes
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from speech_to_video.clients.kling_motion_client import KlingMotionClient  # noqa: E402
from speech_to_video.utils import r2_client  # noqa: E402
from speech_to_video.utils.config import get_settings  # noqa: E402

MODEL = "gemini-3-pro-image-preview"

DEFAULT_REFERENCE = Path(
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/Thriller.png"
)

# S72: holistic-regen framing (per Memory/feedback_regen_vs_preserve_prompts.md).
# Previous "edit this image" framing kept clipping the head; switching to
# "generate a NEW image based on this reference" gives Gemini freedom to
# choose composition / framing while preserving identity + pose.
# Also lets us explicitly drop ALL iOS UI overlays (status bar, X button,
# caption panel) in one shot instead of asking for piecemeal removal.
THRILLER_EDIT_PROMPT = (
    "Use the attached image as a visual REFERENCE only. Generate a NEW clean "
    "photographic image with the following specifications:\n"
    "- Same young woman as the reference. Preserve her exact face, hair, body "
    "shape, skin tone, and identity.\n"
    "- POSE: standing upright facing the camera, head up looking directly "
    "at the camera, with BOTH ARMS extended WIDE to the sides (full wingspan, "
    "T-pose / arms-spread-eagle position), palms facing forward. Feet hip-"
    "width apart on the floor.\n"
    "- Outfit: off-white vintage-washed cropped graphic tee with a faded "
    "crescent-moon + howling-silhouette graphic on the chest, printed in soft "
    "purple and teal ink (cropped fit). Black-bean shorts (a very dark "
    "brownish-black with subtle burgundy/aubergine undertones, same cut as "
    "the reference). White sneakers.\n"
    "- Background: same indoor setting as the reference — cream-painted wall, "
    "dark wooden door on the right, light beige floor.\n"
    "- COMPOSITION: square or near-square aspect ratio (1:1). The frame MUST "
    "accommodate the full arm wingspan with comfortable room on both LEFT "
    "and RIGHT sides — do NOT clip the fingertips at the side edges. Full "
    "body visible head-to-feet, with headroom above the hair. The entire "
    "face MUST be clearly visible.\n"
    "- CRITICAL: do NOT include any UI elements from the reference. No iOS "
    "status bar, no time/signal/wifi/battery icons, no dark circular "
    "close-button, no title or caption text, no dark UI panel at the bottom. "
    "Output must look like an unaltered camera photograph with no app "
    "interface whatsoever."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

THRILLER_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/thriller/driving_video.mp4"
)

# S72: started as a spike for longer-form Pipeline A (video-orientation + 15s),
# but the v3 + std + video-orientation output came out 784x1168 (portrait,
# inherits driving video aspect 9:16) and lateral gestures clipped. Reverted
# to image-orientation + 10s for production Thriller — gives ~1:1 wider aspect
# matching the past Pipeline A templates. v3 + std stays.
KLING_CHARACTER_ORIENTATION = "video"  # 30s cap; on v2.6 output stays ~1:1 regardless of driving aspect (S58)
KLING_MODE = "pro"                     # S73: bumped std→pro for catalog resolution parity. Std produced 960×960 @ 3.3 Mbps, visibly lower-res than past viral_dances previews (1300-1500px @ 17-30 Mbps). Pro brings preview in line with the catalog at ~$1 extra Kling-side per gen. (Thriller's existing published preview is still the std-mode S72 output — re-run pro if quality parity matters.)
KLING_MODEL_NAME = "kling-v2-6"        # S72 Thriller: v2.6 chosen for this template only — v2.6 outputs ~1:1 wide aspect natively (v3 inherits driving's 9:16 portrait, needs letterbox workaround). Cheaper too. Client default stays "kling-v3".

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _api_key() -> str:
    key = os.environ.get("NBP_API_Key") or os.environ.get("NBP_API_KEY")
    if not key:
        print("FAIL  NBP_API_Key not found in .env", file=sys.stderr)
        sys.exit(2)
    return key


def _save_image(resp, out_dir: Path, prefix: str) -> tuple[bool, str, str]:
    for cand in resp.candidates or []:
        content = getattr(cand, "content", None)
        if content is None:
            continue
        for part in content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                mime = getattr(inline, "mime_type", None) or "image/png"
                ext = "png" if "png" in mime else ("jpg" if "jpeg" in mime else "bin")
                path = out_dir / f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
                path.write_bytes(inline.data)
                return True, str(path), mime
    return False, f"no image part in response: {str(resp)[:300]}", ""


def run_edit(client: genai.Client, reference: Path, out_dir: Path) -> tuple[int, str]:
    log.info("NBP edit submit  model=%s  reference=%s", MODEL, reference)
    log.info("Prompt:\n%s", THRILLER_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        THRILLER_EDIT_PROMPT,
    ]

    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAIL  NBP edit  {type(e).__name__}: {e}  elapsed={elapsed:.1f}s")
        return 1, ""
    elapsed = time.time() - t0

    ok, info, _ = _save_image(resp, out_dir, "thriller_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/thriller-chain/{uuid.uuid4().hex}.png"
    log.info("R2 upload (private)  bucket=%s key=%s", selfies_bucket, key)
    r2_client.upload_file(
        local_path=edited_image_path,
        key=key,
        content_type="image/png",
        bucket=selfies_bucket,
    )
    image_url = r2_client.generate_presigned_get_url(
        key, bucket=selfies_bucket, expires_in=1800,
    )

    client = KlingMotionClient()
    log.info(
        "Kling submit  driving=%s  model=%s  orientation=%s  mode=%s  keep_audio=%s",
        THRILLER_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio,
    )
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=THRILLER_DRIVING_VIDEO,
        character_orientation=KLING_CHARACTER_ORIENTATION,
        mode=KLING_MODE,
        model_name=KLING_MODEL_NAME,
        prompt=GENERIC_KLING_PROMPT,
        keep_original_sound="yes" if keep_audio else "no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(
            f"FAIL  Kling  error={result.get('error')}  "
            f"task_id={result.get('task_id')}  elapsed={elapsed:.1f}s"
        )
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"thriller_chain_{uuid.uuid4().hex[:8]}.mp4"
    log.info("Kling download  %s -> %s", video_url, out_path)
    with requests.get(video_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)

    print(
        f"PASS  Kling  task_id={result['task_id']}  "
        f"duration={result.get('duration')}s  elapsed={elapsed:.1f}s"
    )
    print(f"      saved: {out_path}")
    print(f"\n      Inspect:  open '{out_path}'")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--reference",
        default=str(DEFAULT_REFERENCE),
        help=f"Path to Thriller reference image (default: {DEFAULT_REFERENCE})",
    )
    ap.add_argument(
        "--edited-image",
        help="Path to a previously-approved edited image. Skips NBP, runs Kling only.",
    )
    ap.add_argument("--no-kling", action="store_true", help="Run NBP only, skip Kling")
    ap.add_argument(
        "--keep-audio",
        action="store_true",
        help="Pass keep_original_sound=yes to Kling (default: no)",
    )
    ap.add_argument(
        "--out-dir",
        default=str(Path.home() / "Downloads"),
        help="Where to write outputs (default: ~/Downloads)",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.edited_image:
        edited_path = str(Path(args.edited_image).expanduser())
        if not Path(edited_path).exists():
            print(f"FAIL  edited image not found: {edited_path}", file=sys.stderr)
            return 2
        print(f"SKIP  NBP edit  (reusing {edited_path})")
    else:
        reference = Path(args.reference).expanduser()
        if not reference.exists():
            print(f"FAIL  reference not found: {reference}", file=sys.stderr)
            return 2
        rc, edited_path = run_edit(
            genai.Client(api_key=_api_key()), reference, out_dir,
        )
        if rc != 0:
            return rc

    if args.no_kling:
        print("\nSKIP  Kling  (--no-kling)")
        return 0

    return run_kling(edited_path, out_dir, keep_audio=args.keep_audio)


if __name__ == "__main__":
    raise SystemExit(main())
