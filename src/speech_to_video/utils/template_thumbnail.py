"""First-frame poster thumbnail generation for template tiles (S81).

Extracted from scripts/generate_template_thumbnails.py (S80) so the per-template
seed scripts can produce a poster INLINE — a new template auto-gets its
first-frame thumbnail instead of shipping posterless (black off-screen tile).

Mobile home tiles play a <Video> only while on-screen (to bound iOS decoders).
Off-screen / not-yet-mounted tiles show a STATIC first-frame image so the grid
is never black — matching the competitor's "paused = first frame" look. The
poster is frame 0 of the PREVIEW (what the tile video starts on), so the
poster→video handoff is seamless.

Core op: extract frame 0 of a template's preview video (already on R2), upload
it as `thumbnail.jpg` next to the video, and point Firestore
`assets.thumbnail_url` at it (partial update — sibling asset fields untouched;
bumps updated_at so the /api/templates ETag changes and mobile pulls fresh —
see Memory/reference_firestore_partial_update_etag.md).

Two callers:
  - scripts/generate_template_thumbnails.py — catalog-wide backfill (loops).
  - scripts/seed_<slug>_template.py — single template, inline after upsert.
"""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from . import r2_client
from .template_registry import _doc_ref

log = logging.getLogger(__name__)

THUMB_WIDTH = 720  # shared by tile (~530px @3x) and hero; -2 keeps aspect

_FFMPEG: str | None = None


def _ffmpeg() -> str:
    """Resolve the bundled ffmpeg exe lazily (avoids import-time cost)."""
    global _FFMPEG
    if _FFMPEG is None:
        import imageio_ffmpeg

        _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    return _FFMPEG


def _public_base() -> str:
    return r2_client.public_url("").rstrip("/")


def _key_prefix(asset_url: str) -> str | None:
    """viral-dances/<slug> from a public asset URL, or None."""
    base = _public_base() + "/"
    if not asset_url or not asset_url.startswith(base):
        return None
    key = asset_url[len(base):]            # viral-dances/<slug>/preview_stream.mp4
    return key.rsplit("/", 1)[0]           # viral-dances/<slug>


def is_usable_thumbnail(thumbnail_url: str | None) -> bool:
    """True iff `thumbnail_url` is a real poster URL. A placeholder.example or
    non-http value is NOT a real thumbnail — treat it as missing so it gets
    generated even without force. Used here and by the publish gate
    (scripts/set_template_status.py) to decide whether a poster is needed."""
    u = thumbnail_url or ""
    return u.startswith("http") and "placeholder.example" not in u


def _extract_frame0(src_url: str, out_path: Path) -> bool:
    cmd = [
        _ffmpeg(), "-y", "-ss", "0", "-i", src_url, "-frames:v", "1",
        "-vf", f"scale={THUMB_WIDTH}:-2", "-q:v", "3", str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        log.error("ffmpeg failed: %s", r.stderr.strip().splitlines()[-1:] or r.returncode)
        return False
    return True


def generate_thumbnail(
    template: dict,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> str:
    """Generate the first-frame poster for ONE template.

    `template` is a registry doc dict (must carry `id` + `assets`). Source is
    `assets.preview_video_url` (the ~5 Mbps stream the tile plays), falling back
    to `driving_video_url`; the R2 object must already exist. Returns one of
    "ok" | "skipped" | "failed". Does NOT raise on ffmpeg failure (returns
    "failed") — callers decide whether a missing poster is fatal.

    Idempotent: skips when a usable thumbnail_url already exists, unless force.
    Seeds pass force=True because the fixture always writes thumbnail_url=None
    and a re-seed should rebuild the poster too.
    """
    tid = template["id"]
    a = template.get("assets") or {}
    if is_usable_thumbnail(a.get("thumbnail_url")) and not force:
        log.info("SKIP %s (already has usable thumbnail_url)", tid)
        return "skipped"

    src = a.get("preview_video_url") or a.get("driving_video_url")
    prefix = _key_prefix(src or "")
    if not prefix:
        log.warning("SKIP %s (no usable R2 asset url: %s)", tid, src)
        return "skipped"

    thumb_key = f"{prefix}/thumbnail.jpg"
    thumb_url = r2_client.public_url(thumb_key)

    if dry_run:
        log.info("DRY %s  frame0(%s) -> %s", tid, (src or "").rsplit("/", 1)[-1], thumb_key)
        return "ok"

    from firebase_admin import firestore as fb_firestore

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"{tid}.jpg"
        if not _extract_frame0(src, out):
            return "failed"
        r2_client.upload_file(str(out), thumb_key, content_type="image/jpeg")
        _doc_ref(tid).update({
            "assets.thumbnail_url": thumb_url,
            "updated_at": fb_firestore.SERVER_TIMESTAMP,
        })
        log.info("OK   %s -> %s (%d bytes)", tid, thumb_key, out.stat().st_size)
    return "ok"
