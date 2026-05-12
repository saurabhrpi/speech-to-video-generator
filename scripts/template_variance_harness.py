"""Variance-testing harness for per-template QA (AIV-16).

Runs N selfies × N templates through the V2 dispatcher and dumps a comparison
grid for manual QA. Per-template QA gate before flipping `published_status:
published` — gauges output consistency across selfie variance.

CLI:
    python scripts/template_variance_harness.py \\
        --templates viral-dances-bombale[,another-template] \\
        --selfies path/to/selfies-dir/ \\
        --out results/run-001/ \\
        [--confirm] [--dry-run] [--cleanup-r2]

Behavior:
- Validates every --template exists in the registry (404 fast on typo).
- Globs --selfies dir for image files.
- Prints a cost estimate (COGS × cells). Halts unless --confirm or --dry-run.
- Uploads each selfie once to the R2 selfies bucket under
  `selfies/harness-{run_id}/{basename}{ext}`, then iterates pairs sequentially.
- Failures don't abort; recorded in manifest.json + flagged in index.html.
- Output dir layout:
    results/run-001/
      manifest.json
      index.html
      {template_id}/
        {selfie_basename}.mp4

Dry-run mode (--dry-run): skips R2 + dispatcher entirely; copies a known sample
mp4 into each cell so we can validate manifest/HTML/dir layout end-to-end
without real spend or needing Track 2 assets.

Acceptance (per AIV-16): run 1 template × 3 selfies for Pipeline A AND
Pipeline B. Pipeline A real-gen blocks on real Bombale assets (AIV-84 #1).
Pipeline B real-gen blocks on a seeded Pipeline B template.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore")

import requests  # noqa: E402

from src.speech_to_video.utils import template_registry  # noqa: E402
from src.speech_to_video.utils.config import get_settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger("variance-harness")

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
IMG_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

# Rough COGS per dispatcher call. Tune as real numbers land. Used only for the
# pre-run cost estimate / confirm gate — does NOT bill anything.
COGS_PER_GEN_USD = 0.50
WARN_THRESHOLD_USD = 5.00

DRYRUN_SAMPLE_MP4 = ROOT / "docs/research/Kling_MotionControl_Image_Output.mp4"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--templates", required=True, help="Comma-separated template_ids.")
    p.add_argument("--selfies", required=True, type=Path, help="Directory of selfie image files.")
    p.add_argument("--out", required=True, type=Path, help="Output directory for results.")
    p.add_argument("--confirm", action="store_true", help="Confirm spend above the warn threshold.")
    p.add_argument("--dry-run", action="store_true", help="Skip R2 + dispatcher; copy a sample mp4 instead.")
    p.add_argument("--cleanup-r2", action="store_true", help="Delete uploaded selfies from R2 at end.")
    return p.parse_args()


def _discover_selfies(selfies_dir: Path) -> List[Path]:
    if not selfies_dir.is_dir():
        raise SystemExit(f"--selfies must be a directory; got {selfies_dir}")
    found = sorted(
        p for p in selfies_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )
    if not found:
        raise SystemExit(f"no image files in {selfies_dir} (expected {sorted(IMG_EXTS)})")
    return found


def _validate_templates(template_ids: List[str]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for tid in template_ids:
        try:
            out[tid] = template_registry.get_template(tid)
        except template_registry.TemplateNotFound:
            raise SystemExit(f"template_not_found: {tid}")
    return out


def _upload_selfies(selfies: List[Path], run_id: str) -> Dict[Path, str]:
    """Upload each selfie once to R2; return {local_path: r2_key}."""
    from src.speech_to_video.utils import r2_client

    settings = get_settings()
    prefix = f"selfies/harness-{run_id}/"
    out: Dict[Path, str] = {}
    for selfie in selfies:
        ext = selfie.suffix.lower()
        key = f"{prefix}{selfie.stem}{ext}"
        r2_client.upload_bytes(
            selfie.read_bytes(),
            key,
            content_type=IMG_MIME.get(ext, "application/octet-stream"),
            bucket=settings.r2_selfies_bucket,
            cache_control="private, max-age=86400",
        )
        out[selfie] = key
        log.info("uploaded %s -> %s", selfie.name, key)
    return out


def _delete_selfies(keys: List[str]) -> None:
    from src.speech_to_video.utils import r2_client

    settings = get_settings()
    for key in keys:
        try:
            r2_client.delete_object(key, bucket=settings.r2_selfies_bucket)
        except Exception as exc:
            log.warning("failed to delete %s: %s", key, exc)


def _download(url: str, out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = 0
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
    return total


def _run_pair(
    template_id: str,
    selfie_path: Path,
    selfie_r2_key: Optional[str],
    out_root: Path,
    dry_run: bool,
) -> Dict:
    rel_output = Path(template_id) / f"{selfie_path.stem}.mp4"
    abs_output = out_root / rel_output

    entry: Dict = {
        "template_id": template_id,
        "selfie_path": str(selfie_path),
        "selfie_r2_key": selfie_r2_key,
        "output_rel": str(rel_output),
        "success": False,
        "error": None,
        "gen_time_s": None,
        "task_id": None,
        "video_url": None,
        "size_bytes": None,
    }

    if dry_run:
        if not DRYRUN_SAMPLE_MP4.exists():
            entry["error"] = f"dry-run sample missing: {DRYRUN_SAMPLE_MP4}"
            return entry
        abs_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(DRYRUN_SAMPLE_MP4, abs_output)
        entry["success"] = True
        entry["task_id"] = "dryrun"
        entry["gen_time_s"] = 0.0
        entry["video_url"] = f"file://{DRYRUN_SAMPLE_MP4}"
        entry["size_bytes"] = abs_output.stat().st_size
        return entry

    # Real-gen path. Lazy import — keeps dry-run fast and side-effect free.
    from src.speech_to_video.services.video_service import VideoService

    settings = get_settings()
    service = VideoService(settings)

    t0 = time.time()
    try:
        result = service.generate_template_video(
            template_id=template_id,
            selfie_key=selfie_r2_key,
            prompt_overrides=None,
            on_progress=lambda **kw: log.info("  %s/%s: %s", template_id, selfie_path.name, kw.get("phase")),
        )
    except Exception as exc:
        entry["error"] = f"dispatcher_exception: {exc}"
        entry["gen_time_s"] = round(time.time() - t0, 1)
        return entry
    entry["gen_time_s"] = round(time.time() - t0, 1)

    if not result.get("success"):
        entry["error"] = result.get("error") or f"phase={result.get('phase')}"
        entry["task_id"] = result.get("task_id")
        return entry

    video_url = result.get("video_url")
    entry["video_url"] = video_url
    entry["task_id"] = result.get("task_id")
    try:
        entry["size_bytes"] = _download(video_url, abs_output)
    except Exception as exc:
        entry["error"] = f"download_failed: {exc}"
        return entry

    entry["success"] = True
    return entry


def _write_manifest(out_root: Path, entries: List[Dict], run_meta: Dict) -> None:
    manifest = {
        "run": run_meta,
        "entries": entries,
    }
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2))


def _render_html(out_root: Path, template_ids: List[str], selfies: List[Path], entries: List[Dict]) -> None:
    """Pivot manifest into a grid: rows = selfies, columns = templates."""
    by_pair: Dict[Tuple[str, str], Dict] = {}
    for e in entries:
        by_pair[(e["template_id"], Path(e["selfie_path"]).name)] = e

    def cell(template_id: str, selfie_name: str) -> str:
        e = by_pair.get((template_id, selfie_name))
        if not e:
            return '<td class="missing">—</td>'
        if not e["success"]:
            err = str(e.get("error") or "FAILED").replace("<", "&lt;")
            return f'<td class="fail"><div class="label">FAILED</div><div class="err">{err}</div></td>'
        video_src = e["output_rel"]
        size_kb = (e.get("size_bytes") or 0) // 1024
        meta = f"{e.get('gen_time_s', '?')}s · {size_kb} KB"
        task = e.get("task_id") or ""
        return (
            f'<td class="ok">'
            f'<video controls width="240" preload="metadata"><source src="{video_src}"></video>'
            f'<div class="meta">{meta}</div>'
            f'<div class="task">{task}</div>'
            f'</td>'
        )

    selfie_names = [s.name for s in selfies]

    header = "".join(f"<th>{tid}</th>" for tid in template_ids)
    rows = []
    for sname in selfie_names:
        cells = "".join(cell(tid, sname) for tid in template_ids)
        rows.append(f"<tr><th class='sticky-col'>{sname}</th>{cells}</tr>")

    generated_at = datetime.utcnow().isoformat() + "Z"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Variance grid</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 16px; }}
h1 {{ font-size: 18px; }}
.meta-line {{ color: #666; font-size: 12px; margin-bottom: 12px; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ddd; padding: 6px; vertical-align: top; font-size: 12px; }}
thead th {{ position: sticky; top: 0; background: #fafafa; z-index: 2; }}
.sticky-col {{ position: sticky; left: 0; background: #fafafa; z-index: 1; }}
td.ok video {{ display: block; }}
td.ok .meta {{ color: #666; font-size: 11px; margin-top: 4px; }}
td.ok .task {{ color: #999; font-size: 10px; font-family: monospace; }}
td.fail {{ background: #fff3f3; color: #a00; }}
td.fail .err {{ font-size: 10px; font-family: monospace; max-width: 240px; word-break: break-all; }}
td.missing {{ color: #ccc; text-align: center; }}
</style></head>
<body>
<h1>Template variance grid</h1>
<div class="meta-line">Generated {generated_at} UTC · {len(template_ids)} templates × {len(selfie_names)} selfies = {len(template_ids) * len(selfie_names)} cells</div>
<table>
<thead><tr><th>selfie ↓ / template →</th>{header}</tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
</body></html>"""
    (out_root / "index.html").write_text(html)


def main() -> int:
    args = _parse_args()
    template_ids = [t.strip() for t in args.templates.split(",") if t.strip()]
    if not template_ids:
        raise SystemExit("--templates is empty")

    selfies = _discover_selfies(args.selfies)
    templates = _validate_templates(template_ids)
    n_cells = len(template_ids) * len(selfies)

    est_usd = round(n_cells * COGS_PER_GEN_USD, 2)
    log.info(
        "%d templates × %d selfies = %d cells (est. %s)",
        len(template_ids), len(selfies), n_cells,
        f"${est_usd} COGS" if not args.dry_run else "DRY RUN — $0",
    )
    if not args.dry_run and est_usd > WARN_THRESHOLD_USD and not args.confirm:
        raise SystemExit(
            f"estimated spend ${est_usd} exceeds ${WARN_THRESHOLD_USD} threshold; pass --confirm to proceed"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    selfie_keys: Dict[Path, str] = {}
    if not args.dry_run:
        selfie_keys = _upload_selfies(selfies, run_id)

    entries: List[Dict] = []
    for tid in template_ids:
        for selfie in selfies:
            label = f"{tid}/{selfie.name}"
            log.info("running %s", label)
            entry = _run_pair(
                tid, selfie, selfie_keys.get(selfie), args.out, args.dry_run,
            )
            if entry["success"]:
                log.info("  ✓ %s -> %s", label, entry["output_rel"])
            else:
                log.warning("  ✗ %s -> %s", label, entry["error"])
            entries.append(entry)

    run_meta = {
        "run_id": run_id,
        "templates": template_ids,
        "selfies": [str(s) for s in selfies],
        "dry_run": args.dry_run,
        "pipelines": sorted({t.get("pipeline_class") for t in templates.values()}),
    }
    _write_manifest(args.out, entries, run_meta)
    _render_html(args.out, template_ids, selfies, entries)
    log.info("wrote %s/manifest.json + index.html", args.out)

    if args.cleanup_r2 and selfie_keys:
        _delete_selfies(list(selfie_keys.values()))
        log.info("cleaned up %d R2 selfies", len(selfie_keys))

    n_ok = sum(1 for e in entries if e["success"])
    log.info("done: %d/%d cells OK", n_ok, len(entries))
    return 0 if n_ok == len(entries) else 1


if __name__ == "__main__":
    raise SystemExit(main())
