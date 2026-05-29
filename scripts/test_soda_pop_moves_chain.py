"""V2 Pipeline A Soda Pop Moves template — NBP-edit -> Kling Motion Control chain (S83).

Tiktok_dances category template (third Soda Pop variant after viral-dances-soda-
pop-baby-dance and viral-dances-soda-pop-energy). Sister to
scripts/test_got_2_luv_u_chain.py / scripts/test_luku_chain.py (Pattern B —
holistic regen, DIFFERENT subject).

Source: competitor-app screen recording of a young white woman dancing in an
upscale evening restaurant / cafe with tropical plants — long straight chestnut
hair, black spaghetti-strap cami, pink-cream tweed pencil skirt, dainty pearl
drop earrings + small pendant necklace. The dance is cute TikTok-glam hand
framing / face-frame gestures. Static camera, ~1:1 aspect (1284x1398), 9.9s
after a 0.5s start-trim.

Pattern B holistic regen — DIFFERENT subject, DIFFERENT scene, DIFFERENT
wardrobe register:
- Subject: DIFFERENT white woman, long dark hair, slim build (source has
  long chestnut hair; swap to clearly darker, distinct identity).
- Wardrobe: a fitted COCKTAIL MINI DRESS (single piece) — emerald green,
  champagne, or burgundy; thin straps; mid-thigh hem. Source = TWO pieces
  (cami + pencil skirt); swap to a single-piece dress with a distinct color
  register.
- Scene: a HOTEL LOBBY — polished marble floor, a tall chandelier with warm
  glow above, marble columns, large mirror or framed art on a neutral wall,
  soft warm ambient light, blurred sense of luxury in the background.
  Distinct from any restaurant / cafe / cocktail-lounge composition (source's
  register, Freeze's register, Copacabana's register).

⚠️ S83 lateral-room clause (per Memory/reference_kling_mc_aspect_inherits_nbp.md):
the NBP edit MUST leave generous open marble floor on both left and right of
the subject — face-framing gestures play wide. Bake the wider clause in up
front (mandatory for every new template per S83 finding).

The Kling prompt stays the generic coherence prompt (no-overfit policy per
Memory/feedback_no_overfit_prompts.md). The bespoke edit prompt below is for the
MARKETING PREVIEW asset only.

Usage:
    .venv/bin/python scripts/test_soda_pop_moves_chain.py --no-kling
    .venv/bin/python scripts/test_soda_pop_moves_chain.py --edited-image ~/Downloads/soda_pop_moves_edit_xxx.png --keep-audio
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
    "/Users/saurabhsmacbookair/Downloads/App Templates Prep/soda_pop_moves_first_frame.png"
)

# Pattern B — holistic regen, DIFFERENT subject. White woman with long DARK
# hair in a HOTEL LOBBY, fitted cocktail mini dress. Lateral-room clause baked in.
SODA_POP_MOVES_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT young woman — white / fair "
    "complexion, early-to-mid 20s, slim build, with long DARK BRUNETTE hair "
    "(clearly darker than the input's chestnut). Soft warm features, subtle "
    "makeup, a confident relaxed smile. She must be clearly a different "
    "person from the one in the input. Standing upright facing the camera, "
    "full body visible from head to feet. Dainty stud or thin-drop earrings, "
    "delicate thin necklace optional.\n"
    "- Wardrobe: a fitted COCKTAIL MINI DRESS (a single piece, not a two-"
    "piece), thin straps, mid-thigh hem. Pick ONE cohesive look — e.g. "
    "emerald green satin, deep burgundy crepe, champagne / nude silk, or "
    "midnight-navy crepe. Slim heeled sandals or pumps. NOT the input's "
    "BLACK SPAGHETTI-STRAP CAMI + PINK-CREAM TWEED PENCIL SKIRT. Single "
    "piece dress only. NO brand logos or readable text on the dress; any "
    "embellishment must be a small generic abstract design.\n"
    "- Scene: an upscale HOTEL LOBBY — polished marble or terrazzo floor, a "
    "tall warm-glow CHANDELIER visible above, marble columns or panelled "
    "walls, a large framed art piece or a mirror on a neutral wall in the "
    "background, soft warm AMBIENT light from concealed sconces. Subtle "
    "blurred luxury detail in the depth (e.g. distant lobby furniture or a "
    "reception desk, far away). Distinct from any restaurant / cafe / "
    "cocktail-lounge composition — NO dining tables / chairs / monstera "
    "plants / bistro lights within view. Hotel-lobby register, warm "
    "ambient lighting, dressy-evening mood.\n"
    "- LATERAL ROOM (CRITICAL): frame the subject as a WIDER full-body shot — "
    "FARTHER from the camera and SMALLER in the frame than the input, "
    "occupying roughly the central 55-65% of the frame height, CENTERED "
    "horizontally. Leave GENEROUS, roughly EQUAL open marble FLOOR on BOTH "
    "the LEFT and RIGHT sides — at least the width of her full arm wingspan "
    "on each side, with NOTHING within arm's reach (no columns, no furniture, "
    "no plants). Room for lateral hand-framing gestures in either direction.\n"
    "- FEET AND FLOOR (critical): show the feet FULLY with a clear margin of "
    "marble floor below them — do NOT crop the feet at the bottom edge. Keep "
    "feet >=8-10% of frame height above the bottom.\n"
    "- The face MUST be clearly visible — do not crop the head or chin.\n"
    "- Remove ALL UI overlays from the input: the red recording-indicator "
    "pill (or clock readout) at the top-left, the dark circular X close-button "
    "just below it on the left, and the iPhone status-bar icons (signal / "
    "wifi / battery) at the top-right. Paint over each with what would "
    "naturally be behind it (the hotel lobby interior).\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, no "
    "buttons, no text overlays, no status icons. Just the subject in the "
    "hotel lobby."
)

GENERIC_KLING_PROMPT = (
    "For body parts, wardrobe, or scene elements not visible in the input image, "
    "generate content that is visually coherent with what IS visible — matching "
    "the input's palette, attire register, styling, and aesthetic. Do not introduce "
    "elements that conflict with the visible context."
)

# S77 shape: the chain drives off the RAW SOURCE (raw_source.mp4, runbook step 5).
SODA_POP_MOVES_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/soda-pop-moves/raw_source.mp4"
)

# Kling config (S73 defaults): v2.6 + pro + video-orientation.
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
    log.info("Prompt:\n%s", SODA_POP_MOVES_EDIT_PROMPT)

    mime = mimetypes.guess_type(str(reference))[0] or "image/png"
    contents = [
        types.Part.from_bytes(data=reference.read_bytes(), mime_type=mime),
        SODA_POP_MOVES_EDIT_PROMPT,
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

    ok, info, _ = _save_image(resp, out_dir, "soda_pop_moves_edit")
    if ok:
        print(f"PASS  NBP edit  model={MODEL}  elapsed={elapsed:.1f}s")
        print(f"      saved: {info}")
        return 0, info
    print(f"FAIL  NBP edit  error={info}  elapsed={elapsed:.1f}s")
    return 1, ""


def run_kling(edited_image_path: str, out_dir: Path, keep_audio: bool = False) -> int:
    settings = get_settings()

    selfies_bucket = settings.r2_selfies_bucket
    key = f"spike-outputs/soda-pop-moves-chain/{uuid.uuid4().hex}.png"
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
        SODA_POP_MOVES_DRIVING_VIDEO, KLING_MODEL_NAME, KLING_CHARACTER_ORIENTATION, KLING_MODE, keep_audio,
    )
    log.info("Kling prompt:\n%s", GENERIC_KLING_PROMPT)

    t0 = time.time()
    result = client.generate_and_poll(
        image_url=image_url,
        video_url=SODA_POP_MOVES_DRIVING_VIDEO,
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
    out_path = out_dir / f"soda_pop_moves_chain_{uuid.uuid4().hex[:8]}.mp4"
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
        help=f"Path to Soda Pop Moves reference image (default: {DEFAULT_REFERENCE})",
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
