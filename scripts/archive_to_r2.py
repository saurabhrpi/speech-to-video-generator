"""Archive a local media folder to R2 (private bucket), resumable (S79).

Mirrors a local directory tree to an R2 prefix, preserving relative paths.
Resumable: skips any object already present at the target key (HEAD check),
so re-running after an interruption only uploads what's missing.

Destination: the PRIVATE selfies bucket by default — our R2 API token is
bucket-scoped (see memory reference_r2_tokens_bucket_scoped), so a brand-new
archive bucket would 403. A dedicated archive bucket would need a token-scope
expansion in Cloudflare first.

Usage:
  # dry-run (lists what WOULD upload, no writes):
  .venv/bin/python scripts/archive_to_r2.py --src "<dir>" --prefix template-prep-archive/Done --dry-run
  # real:
  .venv/bin/python scripts/archive_to_r2.py --src "<dir>" --prefix template-prep-archive/Done
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from speech_to_video.utils import r2_client  # noqa: E402

DEFAULT_BUCKET = "speech-to-video-selfies"  # private; token-accessible
SKIP_NAMES = {".DS_Store"}


def _exists(key: str, bucket: str) -> bool:
    try:
        r2_client.head_object(key, bucket=bucket)
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Local directory to archive")
    ap.add_argument("--prefix", required=True, help="R2 key prefix (no leading slash)")
    ap.add_argument("--bucket", default=DEFAULT_BUCKET)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    if not src.is_dir():
        print(f"FAIL  not a directory: {src}", file=sys.stderr)
        return 2
    prefix = args.prefix.strip("/")

    files = [p for p in sorted(src.rglob("*")) if p.is_file() and p.name not in SKIP_NAMES]
    total = len(files)
    uploaded = skipped = 0
    up_bytes = 0
    print(f"Archiving {total} files from {src}\n  -> r2://{args.bucket}/{prefix}/  (dry_run={args.dry_run})\n")

    for i, p in enumerate(files, 1):
        rel = p.relative_to(src).as_posix()
        key = f"{prefix}/{rel}"
        size = p.stat().st_size
        if _exists(key, args.bucket):
            skipped += 1
            print(f"[{i}/{total}] SKIP (exists)  {rel}")
            continue
        if args.dry_run:
            print(f"[{i}/{total}] WOULD UPLOAD  {rel}  ({size:,} B)")
            uploaded += 1
            up_bytes += size
            continue
        r2_client.upload_file(local_path=str(p), key=key, bucket=args.bucket)
        uploaded += 1
        up_bytes += size
        print(f"[{i}/{total}] UPLOADED  {rel}  ({size:,} B)")

    verb = "would upload" if args.dry_run else "uploaded"
    print(f"\nDONE  {verb}={uploaded}  skipped={skipped}  bytes={up_bytes:,} (~{up_bytes/1e9:.2f} GB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
