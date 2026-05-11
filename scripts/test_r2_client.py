"""Smoke test for the R2 client (AIV-12).

Always runs:
- public_url() shape check.

Runs only if R2 env vars are set:
- Upload tiny file -> fetch via public URL -> verify body + Cache-Control.
- Re-fetch -> note CF-Cache-Status (HIT expected once CDN has warmed).
- Cleanup the test object.

Usage:
    .venv/bin/python scripts/test_r2_client.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests  # noqa: E402

from src.speech_to_video.utils.r2_client import (  # noqa: E402
    R2NotConfigured,
    delete_object,
    public_url,
    upload_file,
)


def main():
    expected = "https://assets.speech-2-video.ai/foo/bar.png"
    actual = public_url("foo/bar.png")
    assert actual == expected, f"public_url mismatch: {actual!r}"
    print(f"PASS [public_url]    {actual}")

    test_key = "smoketest/r2_client_check.txt"
    payload = b"R2 smoke test from scripts/test_r2_client.py\n"

    with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as f:
        f.write(payload)
        tmp_path = f.name

    try:
        try:
            url = upload_file(tmp_path, test_key, content_type="text/plain; charset=utf-8")
        except R2NotConfigured as e:
            print(f"\nSKIP [e2e]: {e}")
            print("Set R2 env vars and re-run for upload/fetch/cache-header verification.")
            return 0

        print(f"PASS [upload]        {url}")

        r = requests.get(url, timeout=30)
        r.raise_for_status()
        assert r.content == payload, f"body mismatch: {r.content!r}"
        cc = r.headers.get("Cache-Control", "")
        assert "max-age=31536000" in cc and "immutable" in cc, \
            f"unexpected Cache-Control: {cc!r}"
        print(f"PASS [fetch]         status={r.status_code}  Cache-Control={cc!r}")

        r2 = requests.get(url, timeout=30)
        cf = r2.headers.get("CF-Cache-Status", "(none)")
        marker = "PASS" if cf == "HIT" else "NOTE"
        print(f"{marker} [cdn-warm]    CF-Cache-Status={cf!r}")
        if cf != "HIT":
            print("  CDN may need a moment to warm, or domain not yet routed via CF edge.")

        delete_object(test_key)
        print(f"PASS [cleanup]       deleted {test_key}")

        print("\nAll assertions passed.")
        return 0
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
