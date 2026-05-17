"""V2 Pipeline A Gangsta template — NBP-edit → Kling Motion Control chain.

Asset-prep spike for the Gangsta template (S67). Unlike the Bombale chain
script (`test_aistudio_nbp_kling_chain.py`), this does NOT extrapolate a
selfie into a full-body portrait. Instead, it takes a pre-framed reference
screenshot of a dance pose and:

  1. NBP Edit step — strip the UI overlay (X button + caption strip) baked
     into the source screenshot, swap outfit to a beige/cream variant of the
     same streetwear-blazer style, and swap the brick alley background to a
     different lighter-walled urban alley.
  2. Kling Motion Control step — apply the Gangsta dance motion onto the
     edited character image. character_orientation="image" (Outcome 2 —
     motion-onto-character).

The edit prompt is GANGSTA-SPECIFIC by design — this is one-off template
asset prep, not the runtime dispatcher prompt. The runtime prompt remains
the generic coherence prompt (no-overfit policy).

Driving video URL points at the public templates bucket
(`viral-dances/gangsta/driving_video.mp4`, uploaded via
`scripts/upload_template_assets.py`).

Audio: keep_original_sound="no" per S66 testing policy.

Usage:
    .venv/bin/python scripts/test_gangsta_chain.py
    .venv/bin/python scripts/test_gangsta_chain.py --no-kling
    .venv/bin/python scripts/test_gangsta_chain.py --edited-image ~/Downloads/gangsta_edit_xxx.png
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

DEFAULT_REFERENCE = Path.home() / "Downloads" / "App Templates Prep" / "gangsta_reference.png"

GANGSTA_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Remove the circular X button at the top-left corner.\n"
    "- Remove the dark gradient overlay and all text at the bottom "
    "(the 'Gangsta' title, the caption line, and any emoji).\n"
    "- Change the outfit to a beige/cream blazer over a clean white t-shirt with "
    "light-colored chinos. Keep the same loose, contemporary streetwear-blazer "
    "silhouette as the original.\n"
    "- Change the background to a different urban alleyway with lighter-colored "
    "walls (no brick). Keep the moody, dim, naturalistic urban aesthetic.\n"
    "- Preserve the person's pose, face, hair, and identity exactly. Preserve the "
    "mid-dance body position.\n"
    "- Output a clean photographic frame with no overlays, no UI elements, no text."
)

# Same generic coherence prompt used for Bombale (no-overfit policy — the
# runtime Kling prompt does not change per template).
GANGSTA_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

GANGSTA_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/gangsta/driving_video_10s.mp4"
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


def run_edit(client: genai.Client, reference: Path, out_dir: Path) -> tuple[int, str]:
    log.info("NBP edit submit  model=%s  reference=%s", MODEL, reference)
    log.info("Prompt:\n%s", GANGSTA_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        GANGSTA_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "gangsta_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/gangsta-chain/{uuid.uuid4().hex}.png"
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
    log.info("Kling submit  driving=%s", GANGSTA_DRIVING_VIDEO)
    log.info("Kling prompt:\n%s", GANGSTA_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=GANGSTA_DRIVING_VIDEO,
        character_orientation="image",
        prompt=GANGSTA_KLING_PROMPT,
        keep_original_sound="no",
    )
    elapsed = time.time() - t0

    if not result.get("success"):
        print(
            f"FAIL  Kling  error={result.get('error')}  "
            f"task_id={result.get('task_id')}  elapsed={elapsed:.1f}s"
        )
        return 1

    video_url = result["video_url"]
    out_path = out_dir / f"gangsta_chain_{uuid.uuid4().hex[:8]}.mp4"
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
        help=f"Path to gangsta reference image (default: {DEFAULT_REFERENCE})",
    )
    ap.add_argument(
        "--edited-image",
        help="Path to a previously-approved edited image. Skips NBP, runs Kling only.",
    )
    ap.add_argument("--no-kling", action="store_true", help="Run NBP only, skip Kling")
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

    return run_kling(edited_path, out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
