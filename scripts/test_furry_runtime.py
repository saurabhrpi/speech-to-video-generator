"""S89 — Furry Friends RUNTIME de-risk: pet photo → animal regen → Kling dance.

The furry_friends category's promise: a user uploads a photo of their PET (a
normal quadruped dog/cat), and the runtime motion-transfer makes that same pet
dance like a human. This script validates that the hard transformation actually
works BEFORE we build + seed three templates.

It mirrors the runtime path (video_service._dispatch_motion_transfer):
  1. (optional) NBP text-to-image a realistic "user upload" pet photo.
  2. NBP Edit regen using the EXACT runtime animal core
     (VideoService._GENERIC_NBP_REGEN_PROMPT_ANIMAL) + the per-template framing
     hint — re-poses the quadruped standing upright, full-body, spacious.
  3. Kling Motion Control: character = regen image, driver = the dancing-animal
     clip, character_orientation="video", mode/model from _resolve_kling_settings
     (same as runtime). Output = the user's pet dancing.

Usage:
    .venv/bin/python scripts/test_furry_runtime.py --no-kling      # gen pet + regen only
    .venv/bin/python scripts/test_furry_runtime.py --pet-image ~/Downloads/my_dog.jpg
    .venv/bin/python scripts/test_furry_runtime.py --regen-image ~/Downloads/furry_regen_xxx.png
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from speech_to_video.clients.kling_motion_client import KlingMotionClient  # noqa: E402
from speech_to_video.services.video_service import VideoService  # noqa: E402
from speech_to_video.utils import r2_client  # noqa: E402
from speech_to_video.utils.config import get_settings  # noqa: E402

MODEL = "gemini-3-pro-image-preview"

# Default driver = template 1 (top-dog) dancing-dog clip uploaded to R2.
DEFAULT_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/top-dog/raw_source.mp4"
)

# Per-template framing hint the furry seeds will carry (animal-appropriate).
FURRY_FRAMING_HINT = "Composition: full body standing pose, head to paws."

# Simulated "user upload": a normal quadruped pet in a casual snapshot. This is
# the HARD case (4 legs on the ground → must become an upright dancer).
PET_T2I_PROMPT = (
    "A candid amateur smartphone photo of a happy golden retriever dog standing "
    "on all four legs on a living-room floor, full body visible head to paws, "
    "soft natural daylight from a window, slightly casual imperfect snapshot "
    "framing. Photorealistic, no text, no people."
)

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


def gen_pet(client: genai.Client, out_dir: Path) -> str:
    log.info("NBP T2I (sample pet upload)\nPrompt:\n%s", PET_T2I_PROMPT)
    t0 = time.time()
    resp = client.models.generate_content(
        model=MODEL,
        contents=[PET_T2I_PROMPT],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    ok, info, _ = _save_image(resp, out_dir, "furry_pet_input")
    if not ok:
        print(f"FAIL  pet T2I  {info}")
        sys.exit(1)
    print(f"PASS  pet T2I  elapsed={time.time()-t0:.1f}s\n      saved: {info}")
    return info


def regen(client: genai.Client, pet_path: str, out_dir: Path) -> str:
    prompt = VideoService._GENERIC_NBP_REGEN_PROMPT_ANIMAL
    if FURRY_FRAMING_HINT:
        prompt = f"{prompt}\n\n{FURRY_FRAMING_HINT}"
    log.info("NBP regen (animal core)\nPrompt:\n%s", prompt)
    mime = mimetypes.guess_type(pet_path)[0] or "image/png"
    t0 = time.time()
    resp = client.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=Path(pet_path).read_bytes(), mime_type=mime), prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    ok, info, _ = _save_image(resp, out_dir, "furry_regen")
    if not ok:
        print(f"FAIL  regen  {info}")
        sys.exit(1)
    print(f"PASS  regen  elapsed={time.time()-t0:.1f}s\n      saved: {info}")
    return info


def run_kling(regen_path, driving_video, out_dir, mode=None, model_name=None, label="furry_runtime"):
    settings = get_settings()
    if not mode or not model_name:
        svc = VideoService()
        rmodel, rmode = svc._resolve_kling_settings({})  # global runtime settings
        model_name = model_name or rmodel
        mode = mode or rmode
    log.info("Kling settings: model=%s mode=%s", model_name, mode)

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/furry-runtime/{uuid.uuid4().hex}.png"
    r2_client.upload_file(local_path=regen_path, key=key, content_type="image/png", bucket=selfies_bucket)
    image_url = r2_client.generate_presigned_get_url(key, bucket=selfies_bucket, expires_in=1800)

    client = KlingMotionClient()
    log.info("Kling submit  driver=%s  model=%s  mode=%s  orientation=video", driving_video, model_name, mode)
    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=driving_video,
        character_orientation="video",
        mode=mode,
        model_name=model_name,
        prompt=(
            "For body parts, fur, or scene elements not visible in the input image, "
            "generate content that is visually coherent with what IS visible — matching "
            "the input's palette, fur, and aesthetic. Do not introduce elements that "
            "conflict with the visible context."
        ),
        keep_original_sound="yes",
    )
    elapsed = time.time() - t0
    if not result.get("success"):
        print(f"FAIL  Kling  error={result.get('error')}  task_id={result.get('task_id')}  elapsed={elapsed:.1f}s")
        return 1
    out_path = out_dir / f"{label}_{uuid.uuid4().hex[:8]}.mp4"
    with requests.get(result["video_url"], stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)
    print(f"PASS  Kling  task_id={result['task_id']}  duration={result.get('duration')}s  elapsed={elapsed:.1f}s")
    print(f"      saved: {out_path}")
    print(f"\n      Inspect:  open '{out_path}'")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pet-image", help="Use this pet photo instead of generating one")
    ap.add_argument("--regen-image", help="Skip pet+regen, run Kling on this regen image")
    ap.add_argument("--driving-video", default=DEFAULT_DRIVING_VIDEO)
    ap.add_argument("--no-kling", action="store_true", help="Stop after regen")
    ap.add_argument("--mode", help="Kling mode override (e.g. pro); default: resolved runtime")
    ap.add_argument("--model-name", help="Kling model override (e.g. kling-v2-6); default: resolved runtime")
    ap.add_argument("--label", default="furry_runtime", help="Output filename prefix")
    ap.add_argument("--out-dir", default=str(Path.home() / "Downloads"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    client = genai.Client(api_key=_api_key())

    if args.regen_image:
        regen_path = str(Path(args.regen_image).expanduser())
    else:
        pet_path = str(Path(args.pet_image).expanduser()) if args.pet_image else gen_pet(client, out_dir)
        regen_path = regen(client, pet_path, out_dir)

    if args.no_kling:
        print("\nSKIP  Kling  (--no-kling)")
        return 0
    return run_kling(regen_path, args.driving_video, out_dir,
                     mode=args.mode, model_name=args.model_name, label=args.label)


if __name__ == "__main__":
    raise SystemExit(main())
