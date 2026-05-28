"""V2 Pipeline A Dale Pa Ve template — NBP-edit -> Kling Motion Control chain (S82).

Sixth template of the tiktok_dances category. Sister to
scripts/test_freeze_chain.py (Pattern B — holistic regen, DIFFERENT subject;
source is an identifiable real creator).

Source (DRIVING / motion only): competitor-app screen recording of a young man
dancing on a beach, static camera, ~15.0s after a 1s start-trim. Kling is
Outcome-2 (motion-onto-character) so the OUTPUT scene comes from the regen'd
character image, NOT the driving video's beach.

S82 user direction: regen the character as a young LATINA woman in a bright
DANCE / ZUMBA STUDIO, wardrobe INSPIRED BY (not an exact copy of) a fitted red
long-sleeve crop top + baggy wide-leg jeans. Bright indoor daylight scene (no
night-relight needed). The bottoms' printed text in the reference is dropped per
the no-readable-text rule.

The Kling prompt stays the generic coherence prompt (no-overfit policy per
Memory/feedback_no_overfit_prompts.md). The bespoke edit prompt below is for the
MARKETING PREVIEW asset only.

Usage:
    .venv/bin/python scripts/test_dale_pa_ve_chain.py --no-kling
    .venv/bin/python scripts/test_dale_pa_ve_chain.py --edited-image ~/Downloads/dale_pa_ve_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/dale_pa_ve_ref.png"
)

# Pattern B — holistic regen, DIFFERENT subject (S82). Full subject + scene swap:
# the source is a man on a beach; regen as a young Latina woman in a bright dance
# studio. Wardrobe inspired-by (not exact) a red long-sleeve crop + baggy jeans.
# Bright indoor daylight (no night-relight). S78 roomy composition + feet-visible.
# Hybrid-permissive menus per feedback_nbp_hybrid_default.md.
DALE_PA_VE_EDIT_PROMPT = (
    "Edit this image — fully replace the subject AND the background:\n"
    "- Replace the subject with a young LATINA woman — warm tan skin tone, "
    "approximately early-to-mid 20s, slim athletic build, with a confident "
    "expression. Long dark hair (e.g. sleek straight, loose waves, or a high "
    "ponytail — pick one). She is a brand-new person (this is a full regen, not "
    "the input man). Upright standing dance pose, facing the camera, full body "
    "visible from head to feet.\n"
    "- Wardrobe: a trendy dance-studio outfit INSPIRED BY but NOT an exact copy "
    "of a fitted red long-sleeve mock-neck crop top with baggy wide-leg low-rise "
    "jeans. Vary it — e.g. a red ribbed long-sleeve crop top, a burgundy "
    "mock-neck crop, or a fitted red athletic crop — paired with baggy wide-leg "
    "or loose straight blue jeans, and clean sneakers. NO brand logos and NO "
    "readable text anywhere on the clothing (the jeans must have NO printed "
    "words); any graphic must be a small generic abstract design.\n"
    "- Scene: a bright indoor dance / fitness (Zumba) studio — light wood or "
    "vinyl floor, a large wall mirror, plain bright walls, even natural studio "
    "lighting. Genuine bright indoor lighting on the subject, exposed "
    "consistently with the room. Replace the beach entirely.\n"
    "- Frame her as a WIDER full-body shot — FARTHER from the camera and SMALLER "
    "in the frame, occupying roughly the central 55-65% of the frame height, and "
    "CENTERED horizontally. Leave GENEROUS, roughly EQUAL open floor on BOTH the "
    "left and right sides, plus clear floor below the feet — room for lateral "
    "dance movement and a full arm wingspan in either direction. Nothing within "
    "arm's reach on either side.\n"
    "- FEET AND FLOOR (critical): show the feet FULLY with a clear margin of "
    "floor below them — do NOT crop the feet at the bottom edge. Keep feet "
    ">=8-10% of frame height above the bottom.\n"
    "- The face MUST be clearly visible — do not crop the head or chin.\n"
    "- Remove ALL UI overlays from the input: the red recording-indicator pill / "
    "timer at the top-left, the dark circular X close-button just below it at the "
    "top-left, and the iPhone status-bar icons (signal / wifi / battery) at the "
    "top-right. Paint over each with what would naturally be behind it.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, no "
    "buttons, no text overlays, no status icons. Just the woman in the studio."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

# S77 shape: the chain drives off the RAW SOURCE (raw_source.mp4, runbook step 5).
# Kling's OUTPUT is what later gets uploaded as driving_video.mp4.
DALE_PA_VE_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/dale-pa-ve/raw_source.mp4"
)

# Kling config (S73 defaults): v2.6 + pro + video-orientation (driving ~15.0s).
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
    log.info("Prompt:\n%s", DALE_PA_VE_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        DALE_PA_VE_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "dale_pa_ve_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/dale-pa-ve-chain/{uuid.uuid4().hex}.png"
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
        DALE_PA_VE_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio,
    )
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=DALE_PA_VE_DRIVING_VIDEO,
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
    out_path = out_dir / f"dale_pa_ve_chain_{uuid.uuid4().hex[:8]}.mp4"
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
        help=f"Path to Dale Pa Ve reference image (default: {DEFAULT_REFERENCE})",
    )
    ap.add_argument(
        "--edited-image",
        help="Path to a previously-approved edited image. Skips NBP, runs Kling only.",
    )
    ap.add_argument("--no-kling", action="store_true", help="Run NBP only, skip Kling")
    ap.add_argument(
        "--keep-audio",
        action="store_true",
        help="Pass keep_original_sound=yes to Kling (dance templates ship audio ON)",
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
