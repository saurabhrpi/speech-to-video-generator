"""V2 Pipeline A Twist and Shine template — NBP-edit → Kling Motion Control chain (S75).

Sister to scripts/test_cotton_eye_joe_chain.py.

Pattern B (S73 hybrid-permissive): holistic regen with a DIFFERENT subject.
User direction (S75): sunlit indoor studio (wood floor, tall windows, casual
decor) — source was on a sidewalk (pavement); per the dancing-on-pavement
lesson, we move to a dance-appropriate hardwood surface.

Usage:
    .venv/bin/python scripts/test_twist_and_shine_chain.py --no-kling
    .venv/bin/python scripts/test_twist_and_shine_chain.py --edited-image ~/Downloads/twist_and_shine_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/twist_and_shine_frame0.png"
)

TWIST_AND_SHINE_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT young woman — similar age "
    "(approximately early-to-mid 20s), athletic slim build. She must "
    "be clearly a different person from the one in the input "
    "(different facial features, different identity). Long hair "
    "similar in length to the input but in a different color and "
    "style (e.g. honey-blonde with loose waves, dark brown straight, "
    "auburn in a low ponytail, or chestnut-brown with soft curls — "
    "pick one). Same playful, joyful, mid-dance expression — lively "
    "energy. Same general standing dance pose as the input — full "
    "body visible from head to feet.\n"
    "- Wardrobe: STYLE MUST MATCH the input exactly (same casual "
    "summer silhouette: short-sleeve crewneck cotton tee, denim "
    "cutoff shorts, sunglasses, low-top sneakers). Change ONLY the "
    "COLORS — every wardrobe piece must be a different color from "
    "the input. "
    "Tee: NOT the input's white. E.g. soft sage green, dusty rose, "
    "warm rust, or sky blue — pick one. "
    "Denim shorts: NOT the input's light-wash blue. E.g. dark "
    "indigo, medium-wash blue, or warm black denim — pick one. "
    "Sunglasses: keep similar silhouette (cat-eye or round) but in "
    "a different frame color/lens tint than the input (e.g. matte "
    "black, tortoiseshell, gold wire, or amber-tinted — pick one). "
    "Low-top sneakers: NOT the input's white. E.g. black canvas, "
    "tan suede, dark navy, or pastel cream — pick one.\n"
    "- Scene: a SUNLIT INDOOR DANCE STUDIO or CASUAL LOFT INTERIOR "
    "— distinct from the input's outdoor street/sidewalk. Polished "
    "wide-plank HARDWOOD floor, tall floor-to-ceiling windows on "
    "one side letting in warm golden-hour light, light-toned walls "
    "(off-white or warm cream), casual decor in the deep background "
    "(a few framed prints, a plant in the corner, a simple bench "
    "or stool placed FAR from the subject). The subject stands in "
    "the OPEN CENTRAL area of the studio with the hardwood floor "
    "extending well to the LEFT AND RIGHT (at least the subject's "
    "full body-width clear on each side). No furniture, equipment, "
    "or props within arm's reach. CRITICAL: do NOT include mirrors, "
    "mirrored walls, or any reflective surfaces that could show a "
    "reflection of the subject. Warm sunlit atmosphere, intimate "
    "lived-in vibe.\n"
    "- Remove ALL UI overlays from the input: the red recording "
    "indicator at top-center, the dark circular X close-button in "
    "the top-left, and the iPhone status-bar elements at top-right "
    "(signal / wifi / battery icons). Paint over each with what "
    "would naturally be behind it.\n"
    "- Single subject only — do NOT introduce a second person, "
    "duplicate, or mirror image. Just one woman standing in the "
    "studio.\n"
    "- Output a clean photographic frame at square (1:1) aspect — "
    "no UI, no buttons, no text overlays, no status icons. Full body "
    "head-to-feet with comfortable headroom above the hair and "
    "floor visible under the feet. CRITICAL: leave significant clear "
    "floor space on BOTH the LEFT and RIGHT sides of the subject "
    "for lateral dance footwork. The face MUST be clearly visible "
    "(do not crop the head or sunglasses)."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

TWIST_AND_SHINE_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/twist-and-shine/driving_video.mp4"
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
    log.info("Prompt:\n%s", TWIST_AND_SHINE_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        TWIST_AND_SHINE_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "twist_and_shine_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()
    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/twist-and-shine-chain/{uuid.uuid4().hex}.png"
    log.info("R2 upload (private)  bucket=%s key=%s", selfies_bucket, key)
    r2_client.upload_file(local_path=edited_image_path, key=key, content_type="image/png", bucket=selfies_bucket)
    image_url = r2_client.generate_presigned_get_url(key, bucket=selfies_bucket, expires_in=1800)

    client = KlingMotionClient()
    log.info("Kling submit  driving=%s  model=%s  orientation=%s  mode=%s  keep_audio=%s",
        TWIST_AND_SHINE_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio)
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url, video_url=TWIST_AND_SHINE_DRIVING_VIDEO,
        character_orientation=KLING_CHARACTER_ORIENTATION, mode=KLING_MODE,
        model_name=KLING_MODEL_NAME, prompt=GENERIC_KLING_PROMPT,
        keep_original_sound="yes" if keep_audio else "no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(f"FAIL  Kling  error={result.get('error')}  task_id={result.get('task_id')}  elapsed={elapsed:.1f}s")
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"twist_and_shine_chain_{uuid.uuid4().hex[:8]}.mp4"
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
