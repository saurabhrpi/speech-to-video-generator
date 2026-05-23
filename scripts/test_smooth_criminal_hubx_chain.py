"""V2 Pipeline A Smooth Criminal (Hubx redo) — NBP-edit → Kling Motion Control chain (S73).

REPLACES the existing viral-dances-smooth-criminal preview with a longer
(13.69s) version. Same Firestore template_id, same R2 URL — just new file.
Holistic-regen NBP pattern, hybrid-permissive approach (S73 canonical default
per Memory/feedback_nbp_hybrid_default.md).

NBP reference is the trimmed driving video's frame at t=1s (NOT t=0 — the
t=0 frame is chin-cropped, missing the face).

Kling config: v2.6 + pro + video + ≤15s. Driving video is 13.69s.

Usage:
    .venv/bin/python scripts/test_smooth_criminal_hubx_chain.py --no-kling
    .venv/bin/python scripts/test_smooth_criminal_hubx_chain.py --edited-image ~/Downloads/smooth_criminal_hubx_edit_xxx.jpg --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/smooth_criminal_hubx_frame_t1.png"
)

SMOOTH_CRIMINAL_HUBX_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT young woman — late teens or "
    "early 20s, athletic slim build, with different facial features and "
    "different hair from the woman in the input (e.g. dark brown, jet "
    "black, or auburn instead of the input's honey-brown; could be worn "
    "up in a ponytail, half-up, or in a different cut). Same energetic "
    "confident expression, same general mid-dance pose with one arm "
    "raised near the head, full body visible from head to feet.\n"
    "- Wardrobe: a cropped short-sleeve fitted top (e.g. solid bold color "
    "like burgundy, forest green, mustard, or black — pick a register that "
    "is NOT the input's white-with-colorful-graphic; could also be a plain "
    "tank or ribbed knit). Mid-thigh fitted shorts in a complementary tone "
    "(NOT navy velvet — try denim, black athletic, or warm earth tone). "
    "Plain low-top sneakers (any single color other than the input's).\n"
    "- Scene: an indoor casual setting that is DISTINCT from the input's "
    "doorway-on-the-right composition. Pick a different indoor register — "
    "e.g. a sunlit hallway with a window, a small studio with a textured "
    "wall, a loft with exposed brick, or a minimalist bedroom corner. "
    "Soft natural daylight, intimate at-home or studio vibe, light-toned "
    "color palette.\n"
    "- COMPOSITION LOCK (critical): subject must occupy the SAME "
    "proportion of the frame as the woman in the input image — same head "
    "position, same body size relative to the frame edges. Do NOT zoom "
    "in, do NOT zoom out, do NOT move the subject closer to or further "
    "from the camera. Preserve the input's camera-to-subject distance "
    "and framing exactly.\n"
    "- Remove ALL UI overlays from the input: the red recording indicator "
    "at top-center, the iPhone status-bar icons at top-right, and the dark "
    "circular X close-button on the left side. Paint over each with what "
    "would naturally be behind it.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, "
    "no buttons, no text overlays, no status icons. Full body head-to-feet "
    "with comfortable headroom above the hair and floor visible under her "
    "feet. The face MUST be clearly visible (do not crop the head or chin)."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

SMOOTH_CRIMINAL_HUBX_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/smooth-criminal/driving_video.mp4"
)

KLING_CHARACTER_ORIENTATION = "video"
KLING_MODE = "pro"
KLING_MODEL_NAME = "kling-v2-6"

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
    log.info("Prompt:\n%s", SMOOTH_CRIMINAL_HUBX_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        SMOOTH_CRIMINAL_HUBX_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "smooth_criminal_hubx_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/smooth-criminal-hubx-chain/{uuid.uuid4().hex}.png"
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
        SMOOTH_CRIMINAL_HUBX_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio,
    )
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=SMOOTH_CRIMINAL_HUBX_DRIVING_VIDEO,
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
    out_path = out_dir / f"smooth_criminal_hubx_chain_{uuid.uuid4().hex[:8]}.mp4"
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
        help=f"Path to Smooth Criminal Hubx reference image (default: {DEFAULT_REFERENCE})",
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
