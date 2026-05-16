"""Smoke test for Google AI Studio direct — Nano Banana Pro (gemini-3-pro-image-preview).

S65 spike: verify the AI Studio path works without Vertex AI's allowlist gate,
so we can swap the Pipeline B Edit primitive's provider.

Reads NBP_API_Key from .env (case-tolerant fallback to NBP_API_KEY). T2I always
runs and is enough to verify access + auth + non-allowlisted availability. Edit
runs only when both --selfie and --scene are provided.

Usage:
    .venv/bin/python scripts/test_aistudio_nano_banana.py
    .venv/bin/python scripts/test_aistudio_nano_banana.py --selfie /path/to/selfie.jpg --scene /path/to/scene.jpg
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

from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

MODEL = "gemini-3-pro-image-preview"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _api_key() -> str:
    key = os.environ.get("NBP_API_Key") or os.environ.get("NBP_API_KEY")
    if not key:
        print("FAIL  NBP_API_Key not found in .env", file=sys.stderr)
        sys.exit(2)
    return key


def _save_image(resp, out_dir: Path, prefix: str) -> tuple[bool, str, str]:
    """Return (ok, path_or_error, mime)."""
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


def run_t2i(client: genai.Client, prompt: str, out_dir: Path) -> int:
    t0 = time.time()
    log.info("T2I submit model=%s prompt=%r", MODEL, prompt[:80])
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAIL  T2I   {type(e).__name__}: {e}  elapsed={elapsed:.1f}s")
        return 1
    elapsed = time.time() - t0
    ok, info, mime = _save_image(resp, out_dir, "aistudio_t2i")
    if ok:
        print(f"PASS  T2I   model={MODEL}  saved={info}  mime={mime}  elapsed={elapsed:.1f}s")
        return 0
    print(f"FAIL  T2I   error={info}  elapsed={elapsed:.1f}s")
    return 1


def run_edit(client: genai.Client, prompt: str, selfie: Path, scene: Path, out_dir: Path) -> int:
    t0 = time.time()
    log.info("Edit submit model=%s selfie=%s scene=%s", MODEL, selfie, scene)
    contents = []
    for p in (selfie, scene):
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    contents.append(prompt)
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )
    except Exception as e:
        elapsed = time.time() - t0
        print(f"FAIL  Edit  {type(e).__name__}: {e}  elapsed={elapsed:.1f}s")
        return 1
    elapsed = time.time() - t0
    ok, info, mime = _save_image(resp, out_dir, "aistudio_edit")
    if ok:
        print(f"PASS  Edit  model={MODEL}  saved={info}  mime={mime}  elapsed={elapsed:.1f}s")
        return 0
    print(f"FAIL  Edit  error={info}  elapsed={elapsed:.1f}s")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selfie", help="Path to selfie image (Edit smoke)")
    ap.add_argument("--scene", help="Path to scene image (Edit smoke)")
    ap.add_argument(
        "--prompt-t2i",
        default="A red panda eating bamboo in a misty forest, photorealistic, soft morning light",
    )
    ap.add_argument(
        "--prompt-edit",
        default=(
            "Place the person from the first image into the scene from the second image. "
            "Photorealistic. Preserve the person's face and clothing. "
            "Match the lighting and color tone of the scene."
        ),
    )
    ap.add_argument("--out-dir", default="/tmp")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = genai.Client(api_key=_api_key())

    rc = run_t2i(client, args.prompt_t2i, out_dir)
    if rc != 0:
        return rc

    if args.selfie and args.scene:
        rc = run_edit(client, args.prompt_edit, Path(args.selfie), Path(args.scene), out_dir)
    else:
        print("\nSKIP  Edit  (pass --selfie and --scene to exercise Edit mode)")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
