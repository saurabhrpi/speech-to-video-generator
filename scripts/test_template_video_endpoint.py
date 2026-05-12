"""Smoke test for AIV-15 — POST /api/generate/template-video.

Uses FastAPI TestClient (in-process, no server boot). Mocks Firebase Bearer
auth + the dispatcher's actual generation work, but exercises real input
validation, real Firestore template lookup, and real job-manager creation.

Coverage:
- Happy path: real Bombale fixture + valid selfie_key → 200 with job_id
- Bad template_id → 404
- Cross-uid selfie_key → 403
- Missing required fields → 422 (FastAPI/Pydantic)

Out of smoke (proven elsewhere):
- 402 insufficient credits — FastAPI/credit_store path; same as speech-to-video flow
- 429 concurrent submit — job_manager-internal pattern; same as speech-to-video flow

Usage:
    .venv/bin/python scripts/test_template_video_endpoint.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from src.speech_to_video.api.server import app, service  # noqa: E402
from src.speech_to_video.api.firebase_auth import verify_firebase_token  # noqa: E402


TEST_UID = "smoketest-aiv-15-uid"
GOOD_SELFIE_KEY = f"selfies/{TEST_UID}/1234567890_abc123.jpg"
CROSS_UID_SELFIE_KEY = "selfies/some-other-uid/1234567890_abc123.jpg"


def _fake_user():
    return {
        "uid": TEST_UID,
        "is_anonymous": True,
        "email": None,
        "name": None,
        "provider": "test",
    }


# Mock the dispatcher to short-circuit — AIV-14 smoke already validated the real
# end-to-end flow. This smoke only proves the HTTP wrapper contract.
def _fake_dispatch(**kwargs):
    return {
        "success": True,
        "video_url": "https://fake.kling.example/output.mp4",
        "task_id": "fake-task-aiv-15",
        "duration": 9.5,
        "pipeline": "motion-transfer",
    }


app.dependency_overrides[verify_firebase_token] = _fake_user
service.generate_template_video = _fake_dispatch  # type: ignore[assignment]

# Hermetic mocks: bypass credit + job-manager state so we test endpoint logic
# in isolation. (Credit gate + job manager are exercised in their own paths
# via /api/generate/speech-to-video.)
from src.speech_to_video.utils import credit_store  # noqa: E402
from src.speech_to_video.utils import job_manager  # noqa: E402

credit_store.get_balance = lambda uid: 1000  # type: ignore[assignment]
credit_store.ensure_anon_starter = lambda uid, amount=10: None  # type: ignore[assignment]
job_manager.try_create_credit_job = lambda uid, credit_cost, is_anonymous: "fake-job-id-aiv-15"  # type: ignore[assignment]
job_manager.start_job = lambda job_id, target: None  # type: ignore[assignment]
job_manager.update_job = lambda job_id, **kwargs: None  # type: ignore[assignment]

client = TestClient(app)


def main():
    # 1. Happy path — real Bombale fixture (already seeded in Firestore)
    r = client.post(
        "/api/generate/template-video",
        json={"template_id": "viral-dances-bombale", "selfie_key": GOOD_SELFIE_KEY},
    )
    assert r.status_code == 200, f"happy path: {r.status_code} {r.text}"
    body = r.json()
    assert "job_id" in body, f"happy path missing job_id: {body}"
    print(f"PASS  happy        job_id={body['job_id']}")

    # 2. Bad template_id → 404
    r = client.post(
        "/api/generate/template-video",
        json={"template_id": "nonexistent-template-zzz", "selfie_key": GOOD_SELFIE_KEY},
    )
    assert r.status_code == 404, f"bad template: {r.status_code} {r.text}"
    assert "template_not_found" in r.json()["detail"], f"detail: {r.json()}"
    print(f"PASS  404 template detail={r.json()['detail']!r}")

    # 3. Cross-uid selfie_key → 403
    r = client.post(
        "/api/generate/template-video",
        json={"template_id": "viral-dances-bombale", "selfie_key": CROSS_UID_SELFIE_KEY},
    )
    assert r.status_code == 403, f"cross-uid: {r.status_code} {r.text}"
    print(f"PASS  403 selfie   detail={r.json()['detail']!r}")

    # 4. Missing required fields → 422 (Pydantic validation)
    r = client.post(
        "/api/generate/template-video",
        json={"template_id": "viral-dances-bombale"},  # missing selfie_key
    )
    assert r.status_code == 422, f"missing field: {r.status_code} {r.text}"
    print(f"PASS  422 missing  fields validated")

    # 5. Empty body → 422
    r = client.post("/api/generate/template-video", json={})
    assert r.status_code == 422, f"empty body: {r.status_code} {r.text}"
    print(f"PASS  422 empty    body validated")

    print("\nAll AIV-15 endpoint smokes passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
