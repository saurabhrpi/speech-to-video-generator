"""V2 Pipeline A quality spike — NBP-regen → Kling Motion Control chain.

S66 spike (AIV-task#19 from S65): test whether feeding Kling Motion Control a
full-body character image (regenerated from a head-and-shoulders selfie via
Nano Banana Pro Edit) closes the two quality gaps the user flagged on the
Bombale 7/10 output:
  - wardrobe leak (Kling synthesizes shorts despite a kurta-style upper body)
  - knee crop (Kling's dance-shot framing prior stops mid-thigh)

Architectural separation (so this generalizes across all 24 launch templates,
NOT just Bombale):
  - GENERIC_NBP_REGEN_PROMPT — universal core; lives in code.
  - <template>_FRAMING_HINT  — per-template framing line; will move to
    Firestore as e.g. `template.nbp_framing_hint` once architecture lands.
    Bombale's hint here is TEST DATA for this one spike.

Isolation: Kling call uses Bombale's CURRENT prod prompt verbatim (the
"coherence" prompt). NBP regen is the only changed variable vs the existing
7/10 output, so any quality delta attributes cleanly to the NBP step.

Audio: defaults silent (S66 dev/test default). Pass --keep-audio to opt in
(e.g. for re-rendering a launch-ready preview_video.mp4 with the driving
video's soundtrack intact).

Usage:
    # Full chain: NBP + Kling
    .venv/bin/python scripts/test_aistudio_nbp_kling_chain.py \
        --selfie ~/Downloads/Madhvi_selfile.JPG

    # Reuse a previously-approved NBP regen image, skip NBP, just run Kling
    .venv/bin/python scripts/test_aistudio_nbp_kling_chain.py \
        --regen-image ~/Downloads/nbp_regen_627b551e.jpg

    # NBP only (eyeball-before-spending mode)
    .venv/bin/python scripts/test_aistudio_nbp_kling_chain.py \
        --selfie ~/Downloads/Madhvi_selfile.JPG --no-kling
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

GENERIC_NBP_REGEN_PROMPT = (
    "Generate a more complete portrait of this person. Preserve facial identity, "
    "hair, and the visible clothing style. Extrapolate any non-visible body parts, "
    "garments, and footwear in a way that is stylistically continuous with what is "
    "visible."
)

# TEST DATA — Bombale-only framing hint. In prod, this lives per-template in
# Firestore (e.g. template.nbp_framing_hint). Different templates carry
# different hints; some may carry none.
BOMBALE_FRAMING_HINT = "Composition: full body standing pose, head to feet."

# Bombale prod config snapshot (S66, fetched from /api/templates). Same values
# the dispatcher would use today — keeps the Kling call as a faithful A/B
# against the existing 7/10 output.
BOMBALE_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/bombale/driving_video_silent.mp4"
)
BOMBALE_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
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


def run_regen(client: genai.Client, selfie: Path, framing_hint: str, out_dir: Path) -> tuple[int, str]:
    prompt = f"{GENERIC_NBP_REGEN_PROMPT}\n\n{framing_hint}".strip()
    log.info("NBP regen submit  model=%s  selfie=%s", MODEL, selfie)
    log.info("Prompt:\n%s", prompt)

    mime = mimetypes.guess_type(str(selfie))[0] or "image/jpeg"
    contents = [
        types.Part.from_bytes(data=selfie.read_bytes(), mime_type=mime),
        prompt,
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
        print(f"FAIL  NBP regen  {type(e).__name__}: {e}  elapsed={elapsed:.1f}s")
        return 1, ""
    elapsed = time.time() - t0

    ok, info, out_mime = _save_image(resp, out_dir, "nbp_regen")
    if ok:
        print(f"PASS  NBP regen  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP regen  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(regen_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    """Upload regen image to selfies bucket, call Kling Motion Control, save mp4."""
    settings = get_settings()

    # 1. Upload regen image to private selfies bucket and presign for the call.
    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/nbp-kling-chain/{uuid.uuid4().hex}.jpg"
    log.info("R2 upload  bucket=%s key=%s", selfies_bucket, key)
    r2_client.upload_file(
        local_path=regen_image_path,
        key=key,
        content_type="image/jpeg",
        bucket=selfies_bucket,
    )
    image_url = r2_client.generate_presigned_get_url(
        key, bucket=selfies_bucket, expires_in=1800,
    )

    # 2. Kling Motion Control submit + poll.
    client = KlingMotionClient()
    log.info("Kling submit  driving=%s  keep_audio=%s", BOMBALE_DRIVING_VIDEO, keep_audio)
    log.info("Kling prompt:\n%s", BOMBALE_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=BOMBALE_DRIVING_VIDEO,
        character_orientation="image",  # Outcome 2 — motion-onto-character
        prompt=BOMBALE_KLING_PROMPT,
        keep_original_sound="yes" if keep_audio else "no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(f"FAIL  Kling  error={result.get('error')}  task_id={result.get('task_id')}  elapsed={elapsed:.1f}s")
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"nbp_kling_chain_{uuid.uuid4().hex[:8]}.mp4"
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
    ap.add_argument("--selfie", help="Path to source selfie image (input to NBP regen)")
    ap.add_argument(
        "--regen-image",
        help="Path to a previously-approved NBP regen image. If set, skips NBP "
        "and runs only the Kling step on this image.",
    )
    ap.add_argument(
        "--framing-hint",
        default=BOMBALE_FRAMING_HINT,
        help="Per-template framing hint appended to the generic NBP regen prompt",
    )
    ap.add_argument("--no-kling", action="store_true", help="Run NBP only, skip Kling")
    ap.add_argument(
        "--keep-audio",
        action="store_true",
        help="Pass keep_original_sound=yes to Kling (default: no, per S66 test policy)",
    )
    ap.add_argument(
        "--out-dir",
        default=str(Path.home() / "Downloads"),
        help="Where to write outputs (default: ~/Downloads)",
    )
    args = ap.parse_args()

    if not args.selfie and not args.regen_image:
        print("FAIL  pass --selfie or --regen-image", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: NBP regen (skipped if --regen-image provided)
    if args.regen_image:
        regen_path = str(Path(args.regen_image).expanduser())
        if not Path(regen_path).exists():
            print(f"FAIL  regen image not found: {regen_path}", file=sys.stderr)
            return 2
        print(f"SKIP  NBP regen  (reusing {regen_path})")
    else:
        selfie = Path(args.selfie).expanduser()
        if not selfie.exists():
            print(f"FAIL  selfie not found: {selfie}", file=sys.stderr)
            return 2
        rc, regen_path = run_regen(
            genai.Client(api_key=_api_key()), selfie, args.framing_hint, out_dir,
        )
        if rc != 0:
            return rc

    if args.no_kling:
        print("\nSKIP  Kling  (--no-kling)")
        return 0

    return run_kling(regen_path, out_dir, keep_audio=args.keep_audio)


if __name__ == "__main__":
    raise SystemExit(main())
