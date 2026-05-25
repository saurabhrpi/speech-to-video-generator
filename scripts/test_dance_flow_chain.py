"""V2 Pipeline A Dance Flow template — NBP-edit → Kling Motion Control chain (S77).

Sister to scripts/test_na_favelinha_chain.py.

Pattern B (S73 hybrid-permissive) with STRONG similarity constraints. User
direction (S77): replace the man with a DIFFERENT but SIMILAR-LOOKING dude —
same age / height / build — and change the scene to the spacious balcony of a
European seaside HOTEL with a BEACH in the background (source was a European
old-town rooftop).

Source framing note: near full-body, wide lunging dance pose, landscape
(1284x1100). We request square 1:1 for catalog consistency with explicit room
on both sides for the wide pose. Clip is ~10.7s — well under the ~14.5s
end-of-clip duplicate-hallucination zone, so the landscape->square reframing
is low-risk.

Usage:
    .venv/bin/python scripts/test_dance_flow_chain.py --no-kling
    .venv/bin/python scripts/test_dance_flow_chain.py --edited-image ~/Downloads/dance_flow_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/dance_flow_frame0.png"
)

DANCE_FLOW_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT but SIMILAR-LOOKING man — the SAME "
    "age (approximately early 30s), the SAME height and athletic build. He "
    "must be a different individual (different facial features) but in the "
    "same look register: dark hair, clean confident appearance, a relaxed "
    "joyful mid-dance expression. Same general dynamic dance pose as the input "
    "(a wide, energetic lunging stance with arms in motion).\n"
    "- Wardrobe: smart-casual Mediterranean RESORT wear in the same register "
    "as the input — a light, breezy linen shirt with light-toned trousers "
    "(e.g. white linen shirt + beige chinos, pale blue shirt + white "
    "trousers, or sand-colored shirt + cream trousers — pick one). Clean and "
    "summery.\n"
    "- Scene: the SPACIOUS BALCONY or TERRACE of a European seaside HOTEL with "
    "a BEACH and the SEA in the background — a sandy Mediterranean beach and "
    "open ocean horizon beyond a white balustrade railing, warm golden-hour "
    "light, a potted plant or two, an airy resort atmosphere. Distinct from "
    "the input's old-town rooftop view (no church bell tower, no dense town "
    "buildings). The subject stands in the OPEN area of the balcony with clear "
    "space extending to the LEFT AND RIGHT. No furniture within arm's reach.\n"
    "- Remove ALL UI overlays from the input: any close-button and status-bar "
    "icons in the corners. Paint over each with what would naturally be behind "
    "it.\n"
    "- Single subject only — exactly one man, no second person, no duplicate, "
    "no mirror image.\n"
    "- COMPOSITION: keep the man's full body visible from head to feet, at "
    "roughly the same scale and camera-to-subject distance as the input. Leave "
    "comfortable room on BOTH the LEFT and RIGHT sides for the wide lunging "
    "dance pose — do NOT clip his hands or feet at the frame edges.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, no "
    "buttons, no text overlays. The face MUST be clearly visible (do not crop "
    "the head)."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

DANCE_FLOW_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/dance-flow/driving_video.mp4"
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
    log.info("Prompt:\n%s", DANCE_FLOW_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        DANCE_FLOW_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "dance_flow_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()
    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/dance-flow-chain/{uuid.uuid4().hex}.png"
    log.info("R2 upload (private)  bucket=%s key=%s", selfies_bucket, key)
    r2_client.upload_file(local_path=edited_image_path, key=key, content_type="image/png", bucket=selfies_bucket)
    image_url = r2_client.generate_presigned_get_url(key, bucket=selfies_bucket, expires_in=1800)

    client = KlingMotionClient()
    log.info("Kling submit  driving=%s  model=%s  orientation=%s  mode=%s  keep_audio=%s",
        DANCE_FLOW_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio)
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url, video_url=DANCE_FLOW_DRIVING_VIDEO,
        character_orientation=KLING_CHARACTER_ORIENTATION, mode=KLING_MODE,
        model_name=KLING_MODEL_NAME, prompt=GENERIC_KLING_PROMPT,
        keep_original_sound="yes" if keep_audio else "no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(f"FAIL  Kling  error={result.get('error')}  task_id={result.get('task_id')}  elapsed={elapsed:.1f}s")
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"dance_flow_chain_{uuid.uuid4().hex[:8]}.mp4"
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

    return run_kling(edited_path, out_dir, keep_audio=args.keep_audio)


if __name__ == "__main__":
    raise SystemExit(main())
