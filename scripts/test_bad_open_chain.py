"""V2 Pipeline A Bad-Open template — NBP-edit → Kling Motion Control chain (S75).

Sister to scripts/test_bad_chef_chain.py (superseded). Same Bad.mov source,
new creative direction. Reuses bad-chef R2 driving video (same MP4 trimmed
to 15s); rename the R2 path if we publish this variant.

Pattern B (S73 hybrid-permissive): holistic regen with a DIFFERENT subject.
User direction (S75): the man in an open outdoor space (NOT chef / NOT
kitchen). Maximum lateral floor space for the moonwalk to play out.

Kling config DEVIATES from S73 default: this script uses KLING_V3 + pro
to fight the v2.6+pro face-consistency + motion artifacts seen on the
bad-chef variant (reverse moonwalk, face pan, hand disappear). v3+pro is
~$2/gen Kling-side (vs v2.6+pro's ~$1.50).

Usage:
    .venv/bin/python scripts/test_bad_open_chain.py --no-kling
    .venv/bin/python scripts/test_bad_open_chain.py --edited-image ~/Downloads/bad_open_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/bad_chef_frame0.png"
)

BAD_OPEN_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT young man — similar age "
    "(approximately late 20s / early 30s), lean athletic build. He "
    "must be clearly a different person from the one in the input "
    "(different facial features, different identity). Different hair "
    "from the input's short dark crop (e.g. chestnut-brown medium "
    "swept-back, dark wavy mid-length, or a short fade with a clean "
    "edge-up — pick one). May have a short trimmed beard or be "
    "clean-shaven (pick one — different from the input). Same "
    "energetic, playful, confident expression — mid-dance flow, "
    "lively. Same general standing dance pose as the input — low "
    "athletic stance, arms expressive and swinging out from the body, "
    "knees slightly bent, full body visible from head to feet.\n"
    "- Wardrobe: cool casual / streetwear register that is NOT the "
    "input's white tee + brown apron + dark jeans. E.g. a fitted black "
    "crewneck tee with charcoal slim trousers and dark sneakers; or a "
    "vintage-wash denim jacket over a plain off-white tee with dark "
    "tapered jeans and white low-top sneakers; or a soft heather-grey "
    "hoodie with black joggers and dark cross-trainers — pick one. "
    "No apron, no kitchen accessories.\n"
    "- Scene: a WIDE OPEN dance-friendly space — distinct from the "
    "input's outdoor food-truck setting. CRITICAL: the floor must be "
    "a smooth dance-appropriate surface — NOT asphalt, NOT a paved "
    "street, NOT a parking lot. E.g. a large empty warehouse-"
    "converted loft with polished concrete floor, exposed brick walls "
    "in the deep background, and tall industrial windows letting in "
    "cinematic light; or an open ballroom-style hall with polished "
    "hardwood floor, high ceilings, and tall windows letting in "
    "warm golden light (NO mirrors); or an open wooden boardwalk / "
    "pier at sunset with the ocean visible far in the background and "
    "no foot traffic; or a rooftop deck with smooth wood-plank "
    "flooring overlooking a hazy city skyline at golden hour — pick "
    "one. CRITICAL: do NOT include mirrors, mirrored walls, glass "
    "walls, polished metallic surfaces, or any reflective surface "
    "that could show a reflection of the subject. The scene must "
    "contain ONE single subject with no possibility of a second "
    "visual instance via reflection. WIDE OPEN clear floor extending "
    "well to the LEFT AND RIGHT of the subject (at least the "
    "subject's full body-width clear on each side). No furniture, "
    "equipment, vehicles, or props within arm's reach of the "
    "subject. Cool cinematic lighting palette (golden hour, soft "
    "daylight, or warm sunset — pick one matching the chosen scene).\n"
    "- Remove ALL UI overlays from the input: the dark circular X "
    "close-button in the top-left, the iPhone status-bar elements at "
    "the top (the time '7:34' at top-left-center and the signal / "
    "wifi icons at top-right), and the rounded-corner device-frame "
    "border curve at the top. Paint over each with what would "
    "naturally be behind it.\n"
    "- Single subject only — do NOT introduce a second person, "
    "duplicate, or mirror image. Just one man standing in the open "
    "space.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no "
    "UI, no buttons, no text overlays, no status icons. Full body "
    "head-to-feet with comfortable headroom above the hair and "
    "ground visible under the feet. CRITICAL: leave significant "
    "clear ground space on BOTH the LEFT and RIGHT sides of the "
    "subject (the subject will moonwalk laterally across this "
    "ground in the next step — the frame needs ROOM on each side "
    "for that motion). The face MUST be clearly visible (do not "
    "crop the head or chin)."
)

# Final shipping config (S75): v3-pro + Option A's moonwalk-explicit prompt.
# We accepted that none of the experiments (v2.6, v3, prompt-steer, compound
# time-flip) cleanly fixed the depth-axis inversion. v3-pro has the best face/
# motion consistency; Option A's prompt is at minimum a no-op and possibly a
# small positive signal. Defensible per CLAUDE.md preview-vs-runtime split.
GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context. "
    "IMPORTANT MOTION SEMANTICS: the subject is performing the iconic MOONWALK — "
    "the body translates BACKWARD across the floor (away from the direction the "
    "feet appear to be walking) while the feet execute a heel-toe forward-walking "
    "articulation. This is the signature illusion of the moonwalk. Preserve the "
    "source video's exact body-translation direction; do NOT invert backward "
    "body motion to forward body motion. The body must slide BACKWARD, opposite "
    "to the feet's walking-motion direction."
)

# Original (non-reversed) driver. Reuses the bad-chef R2 path (same Bad.mov
# trimmed to 15s); if we publish bad-open, re-upload to its own slug path.
BAD_OPEN_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/bad-chef/driving_video.mp4"
)

KLING_CHARACTER_ORIENTATION = "video"
KLING_MODE = "pro"
KLING_MODEL_NAME = "kling-v3"

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
    log.info("Prompt:\n%s", BAD_OPEN_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        BAD_OPEN_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "bad_open_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/bad-open-chain/{uuid.uuid4().hex}.png"
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
        BAD_OPEN_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio,
    )
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=BAD_OPEN_DRIVING_VIDEO,
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
    out_path = out_dir / f"bad_open_chain_{uuid.uuid4().hex[:8]}.mp4"
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
        help=f"Path to Bad reference image (default: {DEFAULT_REFERENCE})",
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
