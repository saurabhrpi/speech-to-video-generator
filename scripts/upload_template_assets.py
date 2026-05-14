"""Bulk-upload V2 template reference assets to R2 + update Firestore (AIV-88).

Walks a nested base dir of generated template assets, uploads each to the
public R2 templates bucket, and (default) writes the resulting URLs back into
the matching Firestore template doc's `assets.*` slots.

Expected local layout (nested per Q1 decision, S64):

    <base>/<category>/<slug>/<files>

    e.g.  assets/templates/viral-dances/bombale/driving_video.mp4
                                                thumbnail.jpg

The template_id is the flat slug `<category>-<slug>` (e.g. `viral-dances-bombale`)
to match the existing registry convention (`scripts/seed_template_registry.py`).

R2 key mirrors the local nested path: `viral-dances/bombale/driving_video.mp4`.
Public URL is `<R2_PUBLIC_BASE_URL>/<key>`.

## Canonical slot filenames

Each file's basename (without extension) maps to one of four schema slots:

  driving_video   -> assets.driving_video_url    (Pipeline A)
  scene_image     -> assets.scene_image_url      (Pipeline B)
  thumbnail       -> assets.thumbnail_url        (both)
  preview_video   -> assets.preview_video_url    (both, optional)

Allowed extensions:
  video slots: .mp4 .mov .webm
  image slots: .jpg .jpeg .png .webp

## Manifest override (escape hatch for non-canonical filenames)

If `_manifest.json` exists in a template dir, it overrides slot detection:

    {
      "driving_video": "raw_veo_xyz.mp4",
      "thumbnail":     "tile_640.jpg"
    }

Keys are slot names; values are filenames (in the same dir). Files NOT listed
in the manifest are ignored. Files listed but not present on disk are an error.

## Flags

  --dry-run             Plan only. No R2 uploads, no Firestore writes.
  --no-update-registry  Upload to R2 but skip Firestore updates (print URLs).
  --template / -t       Only process given template_id(s). Repeatable.

## Acceptance (AIV-88)

  - Run against a directory containing the Bombale fixture (placeholder content
    OK). All files land at the expected R2 keys; console prints a table of
    (local path, R2 key, public URL). With registry update enabled, the
    Bombale Firestore entry's assets.driving_video_url + assets.thumbnail_url
    flip from `placeholder.example/*` to the real R2 URLs.

## Cache caveat for re-uploads

Templates bucket sets `Cache-Control: public, max-age=31536000, immutable`.
Re-uploading to the SAME key replaces the R2 object but CF edges keep serving
the old version for up to a year. When replacing an asset, either bump the
filename (e.g. `driving_video_v2.mp4`) or purge the CF cache for that URL.

Usage:
    .venv/bin/python scripts/upload_template_assets.py assets/templates/
    .venv/bin/python scripts/upload_template_assets.py assets/templates/ --dry-run
    .venv/bin/python scripts/upload_template_assets.py assets/templates/ -t viral-dances-bombale
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.r2_client import R2NotConfigured  # noqa: E402
from src.speech_to_video.utils.template_registry import (  # noqa: E402
    TemplateNotFound,
    get_template,
    upsert_template,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("upload_template_assets")

SLOT_FIELDS = {
    "driving_video": "driving_video_url",
    "scene_image": "scene_image_url",
    "thumbnail": "thumbnail_url",
    "preview_video": "preview_video_url",
}

VIDEO_EXTS = {".mp4", ".mov", ".webm"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

SLOT_EXTS = {
    "driving_video": VIDEO_EXTS,
    "scene_image": IMAGE_EXTS,
    "thumbnail": IMAGE_EXTS,
    "preview_video": VIDEO_EXTS,
}

MANIFEST_FILENAME = "_manifest.json"


@dataclass
class PlannedUpload:
    template_id: str
    slot: str            # e.g. "driving_video"
    field: str           # e.g. "driving_video_url"
    local_path: Path
    r2_key: str
    public_url: str      # filled after upload (or pre-computed for dry-run)


@dataclass
class TemplatePlan:
    template_id: str
    category: str
    slug: str
    dir_path: Path
    uploads: List[PlannedUpload]
    errors: List[str]


def _discover_template_dirs(base: Path) -> List[tuple]:
    """Yield (category, slug, dir_path) tuples for every <base>/<category>/<slug>/."""
    out = []
    if not base.is_dir():
        raise SystemExit(f"base dir not found: {base}")
    for category_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for slug_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            out.append((category_dir.name, slug_dir.name, slug_dir))
    return out


def _classify_canonical(filename: str) -> Optional[str]:
    """Return slot name if `filename` matches a canonical pattern, else None."""
    p = Path(filename)
    stem, ext = p.stem, p.suffix.lower()
    if stem not in SLOT_FIELDS:
        return None
    if ext not in SLOT_EXTS[stem]:
        return None
    return stem


def _plan_template(category: str, slug: str, dir_path: Path) -> TemplatePlan:
    template_id = f"{category}-{slug}"
    plan = TemplatePlan(
        template_id=template_id,
        category=category,
        slug=slug,
        dir_path=dir_path,
        uploads=[],
        errors=[],
    )

    files = [p for p in dir_path.iterdir() if p.is_file()]
    manifest_path = dir_path / MANIFEST_FILENAME
    slot_to_filename: Dict[str, str] = {}

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError as e:
            plan.errors.append(f"bad {MANIFEST_FILENAME}: {e}")
            return plan
        if not isinstance(manifest, dict):
            plan.errors.append(f"{MANIFEST_FILENAME} must be a JSON object")
            return plan
        for slot, fname in manifest.items():
            if slot not in SLOT_FIELDS:
                plan.errors.append(f"manifest slot {slot!r} not in {sorted(SLOT_FIELDS)}")
                continue
            if not isinstance(fname, str):
                plan.errors.append(f"manifest value for {slot!r} must be a string filename")
                continue
            slot_to_filename[slot] = fname
    else:
        for f in files:
            if f.name == MANIFEST_FILENAME:
                continue
            slot = _classify_canonical(f.name)
            if slot is None:
                log.warning(
                    "  skip non-canonical file %s (use _manifest.json to include)",
                    f.name,
                )
                continue
            if slot in slot_to_filename:
                plan.errors.append(
                    f"duplicate slot {slot!r}: both {slot_to_filename[slot]} and {f.name}"
                )
                continue
            slot_to_filename[slot] = f.name

    if not slot_to_filename and not plan.errors:
        plan.errors.append("no recognized asset files (canonical or via manifest)")
        return plan

    for slot, fname in slot_to_filename.items():
        local = dir_path / fname
        if not local.exists():
            plan.errors.append(f"slot {slot!r} -> missing file {fname}")
            continue
        ext = local.suffix.lower()
        if ext not in SLOT_EXTS[slot]:
            plan.errors.append(
                f"slot {slot!r} -> {fname}: extension {ext!r} not in {sorted(SLOT_EXTS[slot])}"
            )
            continue
        key = f"{category}/{slug}/{fname}"
        plan.uploads.append(
            PlannedUpload(
                template_id=template_id,
                slot=slot,
                field=SLOT_FIELDS[slot],
                local_path=local,
                r2_key=key,
                public_url=r2_client.public_url(key),
            )
        )

    return plan


def _print_plan(plans: List[TemplatePlan]) -> None:
    rows = []
    for p in plans:
        for u in p.uploads:
            rows.append((str(u.local_path), u.r2_key, u.public_url))
    if not rows:
        log.info("(no uploads planned)")
        return
    col1 = max(len(r[0]) for r in rows) + 2
    col2 = max(len(r[1]) for r in rows) + 2
    log.info("")
    log.info("%-*s %-*s %s", col1, "LOCAL", col2, "R2 KEY", "PUBLIC URL")
    log.info("%s", "-" * (col1 + col2 + 60))
    for local_p, key, url in rows:
        log.info("%-*s %-*s %s", col1, local_p, col2, key, url)
    log.info("")


def _execute_uploads(plan: TemplatePlan) -> None:
    for u in plan.uploads:
        url = r2_client.upload_file(str(u.local_path), u.r2_key)
        u.public_url = url


def _update_registry(plan: TemplatePlan) -> bool:
    """Update the Firestore template doc's assets.* slots. Returns True on success.

    upsert_template fully replaces the doc, so we fetch first, mutate assets,
    then write back to preserve every other field (pipeline_class, model, etc.).
    """
    try:
        existing = get_template(plan.template_id)
    except TemplateNotFound:
        log.warning(
            "  registry: template %s not found in Firestore — skipping registry update "
            "(R2 upload succeeded, URLs above)",
            plan.template_id,
        )
        return False

    existing_assets = dict(existing.get("assets") or {})
    for u in plan.uploads:
        existing_assets[u.field] = u.public_url
    existing.pop("id", None)
    existing.pop("created_at", None)
    existing.pop("updated_at", None)
    existing["assets"] = existing_assets

    upsert_template(plan.template_id, existing)
    log.info(
        "  registry: updated %s -> %s",
        plan.template_id,
        ", ".join(f"{u.field}" for u in plan.uploads),
    )
    return True


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Bulk-upload V2 template assets to R2 + update Firestore.")
    ap.add_argument("base_dir", help="Base dir containing <category>/<slug>/ template dirs.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Plan only: no R2 uploads, no Firestore writes.")
    ap.add_argument("--no-update-registry", action="store_true",
                    help="Upload to R2 but skip Firestore template-doc updates.")
    ap.add_argument("-t", "--template", action="append", default=None,
                    help="Only process this template_id (repeatable).")
    args = ap.parse_args(argv)

    base = Path(args.base_dir).resolve()
    template_filter = set(args.template) if args.template else None

    # Fail fast if R2 isn't configured and we'd actually need it.
    if not args.dry_run:
        try:
            r2_client._s3()
        except R2NotConfigured as e:
            log.error("R2 not configured: %s", e)
            return 2

    log.info("scanning %s", base)
    discovered = _discover_template_dirs(base)
    if not discovered:
        log.warning("no <category>/<slug>/ dirs found under %s", base)
        return 0

    plans: List[TemplatePlan] = []
    for category, slug, dir_path in discovered:
        plan = _plan_template(category, slug, dir_path)
        if template_filter and plan.template_id not in template_filter:
            continue
        plans.append(plan)

    if not plans:
        log.warning("no templates matched filter %s", args.template)
        return 0

    # Surface plan errors up front; refuse to upload if any template is broken.
    error_plans = [p for p in plans if p.errors]
    for p in error_plans:
        log.error("template %s (%s):", p.template_id, p.dir_path)
        for e in p.errors:
            log.error("  - %s", e)
    if error_plans:
        log.error("refusing to upload — fix the errors above and re-run")
        return 3

    _print_plan(plans)

    if args.dry_run:
        log.info("DRY RUN — no uploads, no registry updates")
        return 0

    for plan in plans:
        log.info("uploading %s (%d files)", plan.template_id, len(plan.uploads))
        _execute_uploads(plan)
        if not args.no_update_registry:
            _update_registry(plan)

    log.info("")
    log.info("done: %d template(s), %d file(s)",
             len(plans), sum(len(p.uploads) for p in plans))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
