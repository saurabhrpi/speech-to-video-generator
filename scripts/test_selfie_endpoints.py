"""Smoke test for AIV-89 selfie endpoints.

Uses FastAPI TestClient (in-process, no server boot). Mocks Firebase Bearer
auth via app.dependency_overrides so no Firebase token is needed.

Hits the real R2 selfies bucket (cleans up after itself). Requires R2_*
credentials in env + R2 token scoped to the selfies bucket.

Coverage:
- Upload x2 (different content) → 200 + key returned
- List → returns both
- Delete one → list returns one
- Delete all → list returns zero
- Cross-uid delete attempt → 403
- Non-image upload → 400
- Oversized upload → 413

Usage:
    .venv/bin/python scripts/test_selfie_endpoints.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Suppress noisy boto3 deprecation + auto-init Firebase before module-import
import warnings  # noqa: E402
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from src.speech_to_video.api.server import app  # noqa: E402
from src.speech_to_video.api.firebase_auth import verify_firebase_token  # noqa: E402


TEST_UID_A = "smoketest-aiv-89-uid-A"
TEST_UID_B = "smoketest-aiv-89-uid-B"

_active_uid = TEST_UID_A


def _fake_user():
    return {
        "uid": _active_uid,
        "is_anonymous": True,
        "email": None,
        "name": None,
        "provider": "test",
    }


app.dependency_overrides[verify_firebase_token] = _fake_user
client = TestClient(app)


# 1x1 transparent PNG (the smallest valid PNG, ~70 bytes)
_TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c63000100000005000100"
    "0d0a2db40000000049454e44ae426082"
)


def _set_uid(uid: str):
    global _active_uid
    _active_uid = uid


def _upload_one(label: str, body: bytes = _TINY_PNG, content_type: str = "image/png"):
    files = {"file": (f"{label}.png", body, content_type)}
    resp = client.post("/api/upload/selfie", files=files)
    return resp


def _list():
    return client.get("/api/selfies")


def _delete_one(key: str):
    return client.delete("/api/selfies", params={"key": key})


def _delete_all():
    return client.delete("/api/selfies")


def main():
    _set_uid(TEST_UID_A)

    # Tidy up any leftovers from a prior run
    _delete_all()

    # Upload x2
    r = _upload_one("a")
    assert r.status_code == 200, f"upload-a failed: {r.status_code} {r.text}"
    key_a = r.json()["key"]
    print(f"PASS  upload     key={key_a}  size={r.json()['size_bytes']}")

    r = _upload_one("b")
    assert r.status_code == 200, f"upload-b failed: {r.status_code} {r.text}"
    key_b = r.json()["key"]
    print(f"PASS  upload     key={key_b}  size={r.json()['size_bytes']}")

    # List
    r = _list()
    assert r.status_code == 200, f"list failed: {r.status_code} {r.text}"
    listed = {o["key"] for o in r.json()}
    assert key_a in listed and key_b in listed, f"list missing keys: {listed}"
    print(f"PASS  list       count={len(listed)}")

    # Delete one
    r = _delete_one(key_a)
    assert r.status_code == 200, f"delete-one failed: {r.status_code} {r.text}"
    print(f"PASS  delete-one deleted={r.json()['deleted']}")

    r = _list()
    listed = {o["key"] for o in r.json()}
    assert key_a not in listed and key_b in listed, f"after delete-one, listed={listed}"
    print(f"PASS  list       count={len(listed)} (after delete-one)")

    # Cross-uid attempt — switch to uid B and try to delete uid A's remaining key
    _set_uid(TEST_UID_B)
    r = _delete_one(key_b)
    assert r.status_code == 403, f"cross-uid delete should 403; got {r.status_code} {r.text}"
    print(f"PASS  cross-uid  403 enforced on '{key_b}' as uid B")

    # Verify uid B can't see uid A's selfies (list isolation)
    r = _list()
    assert r.status_code == 200
    assert all(not o["key"].startswith(f"selfies/{TEST_UID_A}/") for o in r.json()), \
        f"uid B sees uid A's selfies: {r.json()}"
    print(f"PASS  isolation  uid B does not see uid A's selfies")

    # Switch back to uid A; delete-all
    _set_uid(TEST_UID_A)
    r = _delete_all()
    assert r.status_code == 200, f"delete-all failed: {r.status_code} {r.text}"
    print(f"PASS  delete-all deleted_count={r.json()['deleted_count']}")

    r = _list()
    assert len(r.json()) == 0, f"list after delete-all should be empty: {r.json()}"
    print(f"PASS  list       count=0 (after delete-all)")

    # Validation: non-image upload
    files = {"file": ("foo.txt", b"hello", "text/plain")}
    r = client.post("/api/upload/selfie", files=files)
    assert r.status_code == 400, f"non-image upload should 400; got {r.status_code} {r.text}"
    print(f"PASS  validate   non-image rejected: {r.json()['detail']!r}")

    # Validation: oversized upload (11 MB)
    big = b"A" * (11 * 1024 * 1024)
    files = {"file": ("big.png", big, "image/png")}
    r = client.post("/api/upload/selfie", files=files)
    assert r.status_code == 413, f"oversized upload should 413; got {r.status_code} {r.text}"
    print(f"PASS  validate   oversized rejected: {r.json()['detail']!r}")

    print("\nAll selfie endpoint smokes passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
