"""Purge Cloudflare's edge cache for specific URLs.

The templates R2 bucket sets `Cache-Control: public, max-age=31536000, immutable`,
so CF edges keep serving the old content for up to a year when you overwrite
an R2 object. This script purges specific URLs from the CF cache so you can
re-upload to the SAME key and have users immediately see the new content.

Use sparingly — purge ONLY the URLs you intentionally changed; avoid bulk
purges that would cold-start the cache for unrelated traffic.

Requires in .env:
    CF_API_TOKEN  (with Zone:Cache Purge:Purge permission on the zone)
    CF_ZONE_ID    (e.g. bf29897f... for speech-2-video.ai)

Usage:
    .venv/bin/python scripts/purge_cf_cache.py \
        https://assets.speech-2-video.ai/viral-dances/beat-it/driving_video.mp4 \
        https://assets.speech-2-video.ai/viral-dances/beat-it/preview_video.mp4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+", help="URLs to purge from CF cache")
    args = ap.parse_args()

    token = os.environ.get("CF_API_TOKEN")
    zone = os.environ.get("CF_ZONE_ID")
    if not token or not zone:
        print("FAIL  CF_API_TOKEN and CF_ZONE_ID must be set in .env", file=sys.stderr)
        return 2

    endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone}/purge_cache"
    body = json.dumps({"files": args.urls}).encode()
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        print(f"FAIL  HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"FAIL  {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if not data.get("success"):
        print(f"FAIL  CF errors: {data.get('errors')}", file=sys.stderr)
        return 1

    print(f"PASS  purged {len(args.urls)} URL(s)")
    for u in args.urls:
        print(f"      {u}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
