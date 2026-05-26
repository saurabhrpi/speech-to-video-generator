"""V2 Pipeline A Woman template — NBP-edit → Kling Motion Control chain (S80).

Eighth template of the "Girl Dances" row (category girl_dances).
Sister to scripts/test_pour_it_up_chain.py.

Pattern B (different woman) — the source is an identifiable competitor-app
dancer; we swap in a genuinely different subject, matching the source's wardrobe
register + coverage (change colors only) and its scene register. S78 standing
composition: roomy/wider full-body, centered, feet+floor visible, generous
lateral room (assumes a static-camera upright driver — fall back to
preserve-framing if the source pushes in).

Source: Woman_start_at_0.5_sec.mov (1284×1394 near-square, ~8.6s; trim the first
0.5s per filename → ~8.1s driver). Reference frame = trimmed clip t=0
(woman_ref.png) — the actual driving start frame.

Usage:
    .venv/bin/python scripts/test_woman_chain.py --no-kling
    .venv/bin/python scripts/test_woman_chain.py --edited-image ~/Downloads/woman_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/woman_ref.png"
)

WOMAN_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a GENUINELY DIFFERENT young woman — NOT the "
    "same person as the input. Keep ONLY her age (approximately early-to-mid "
    "20s), her height, and her slim build the same, plus the same general "
    "UPRIGHT STANDING dance pose (she is standing, facing the camera, exactly "
    "as in the input). Everything about her APPEARANCE must clearly differ "
    "from the input:\n"
    "  - Hair: a DIFFERENT color and style from the input — e.g. honey-blonde, "
    "warm caramel, auburn, or a dark sleek ponytail — pick one.\n"
    "  - Skin tone: a natural skin tone clearly different from the input's.\n"
    "  - Different facial features. A confident, upbeat expression. Her face "
    "must be clearly visible, turned toward the camera, and NOT hidden by her "
    "hair.\n"
    "- Wardrobe: MATCH the input's wardrobe STYLE and SKIN COVERAGE — same "
    "garments and same coverage level (do NOT make it more conservative, do "
    "NOT make it more revealing — match it). Change ONLY the colors to a "
    "tasteful different color (pick one). No readable text or logos.\n"
    "- Scene: match the input's setting register but make it a SPACIOUS open "
    "version with a WIDE expanse of open ground/floor extending well to her "
    "LEFT AND RIGHT. Nothing within arm's reach on either side. Keep the "
    "subject clearly lit and well-exposed.\n"
    "- Remove ALL UI overlays from the input: any recording indicator, close "
    "button, captions, and status-bar elements (signal / wifi / battery "
    "icons). Paint over each with what would naturally be behind it.\n"
    "- Single subject only — exactly one woman, no second person, no duplicate, "
    "no mirror image.\n"
    "- COMPOSITION: frame her a bit CLOSER than a full-body shot — a medium "
    "shot where she occupies roughly the central 70-85% of the frame height, "
    "CENTERED horizontally with comfortable room on both sides for lateral "
    "movement. Her face and her raised arms/hands must stay FULLY in frame "
    "with clear headroom above.\n"
    "- Feet do NOT need to be visible — it is fine to crop at the shins or "
    "knees at the bottom edge. Do NOT crop the head, chin, or hands/arms.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, no "
    "buttons, no text overlays. The face MUST be clearly visible (do not crop "
    "the head or chin)."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

# S77 flow: chain drives off the trimmed RAW source (raw_source.mp4); the
# high-bitrate Kling output is later uploaded as driving_video.mp4 (runtime driver).
WOMAN_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/woman/raw_source.mp4"
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
    log.info("Prompt:\n%s", WOMAN_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        WOMAN_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "woman_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False,
              driving_video: str = WOMAN_DRIVING_VIDEO) -> int:
    settings = get_settings()
    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/woman-chain/{uuid.uuid4().hex}.png"
    log.info("R2 upload (private)  bucket=%s key=%s", selfies_bucket, key)
    r2_client.upload_file(local_path=edited_image_path, key=key, content_type="image/png", bucket=selfies_bucket)
    image_url = r2_client.generate_presigned_get_url(key, bucket=selfies_bucket, expires_in=1800)

    client = KlingMotionClient()
    log.info("Kling submit  driving=%s  model=%s  orientation=%s  mode=%s  keep_audio=%s",
        driving_video, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio)
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url, video_url=driving_video,
        character_orientation=KLING_CHARACTER_ORIENTATION, mode=KLING_MODE,
        model_name=KLING_MODEL_NAME, prompt=GENERIC_KLING_PROMPT,
        keep_original_sound="yes" if keep_audio else "no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(f"FAIL  Kling  error={result.get('error')}  task_id={result.get('task_id')}  elapsed={elapsed:.1f}s")
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"woman_chain_{uuid.uuid4().hex[:8]}.mp4"
    log.info("Kling download  %s -> %s", video_url, out_path)
    with requests.get(video_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                f.write(chunk)

    print(f"PASS  Kling  task_id={result['task_id']}  duration={result.get('duration')}s  elapsed={elapsed:.1f}s")
    print(f"      saved: {out_path}")
    print(f"\n      Inspect:  open '{out_path}'")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    ap.add_argument("--edited-image")
    ap.add_argument("--no-kling", action="store_true")
    ap.add_argument("--keep-audio", action="store_true")
    ap.add_argument("--driving-video", default=WOMAN_DRIVING_VIDEO,
                    help="Driving video URL (override to use an upscaled driver)")
    ap.add_argument("--out-dir", default=str(Path.home() / "Downloads"))
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
        rc, edited_path = run_edit(genai.Client(api_key=_api_key()), reference, out_dir)
        if rc != 0:
            return rc

    if args.no_kling:
        print("\nSKIP  Kling  (--no-kling)")
        return 0

    return run_kling(edited_path, out_dir, keep_audio=args.keep_audio,
                     driving_video=args.driving_video)


if __name__ == "__main__":
    raise SystemExit(main())
