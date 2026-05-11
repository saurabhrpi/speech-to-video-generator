"""Smoke test for Vertex AI auth (AIV-79).

Verifies that the service account JSON in env can authenticate against the
Vertex AI endpoint and complete one cheap text-only call.

Auth precedence (mirrors Firebase pattern in api/firebase_auth.py):
1. VERTEX_SERVICE_ACCOUNT_JSON  — full JSON string (Replit prod)
2. VERTEX_SERVICE_ACCOUNT_PATH  — path on disk (local dev convenience)

Required env:
- GOOGLE_CLOUD_PROJECT        — GCP project ID
- VERTEX_LOCATION             — region (default `us-central1`)
- VERTEX_SERVICE_ACCOUNT_JSON or VERTEX_SERVICE_ACCOUNT_PATH

Usage:
    .venv/bin/python scripts/test_vertex_auth.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils.config import get_settings  # noqa: E402


def _load_credentials(s):
    from google.oauth2 import service_account
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    if s.vertex_service_account_json:
        info = json.loads(s.vertex_service_account_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        return creds, "VERTEX_SERVICE_ACCOUNT_JSON", info.get("client_email", "?")

    if s.vertex_service_account_path:
        path = os.path.expanduser(s.vertex_service_account_path)
        with open(path) as f:
            info = json.load(f)
        creds = service_account.Credentials.from_service_account_file(path, scopes=scopes)
        return creds, f"VERTEX_SERVICE_ACCOUNT_PATH={path}", info.get("client_email", "?")

    print("FAIL [env]  Set VERTEX_SERVICE_ACCOUNT_JSON or VERTEX_SERVICE_ACCOUNT_PATH")
    sys.exit(2)


def main():
    s = get_settings()

    if not s.google_cloud_project:
        print("FAIL [env]  GOOGLE_CLOUD_PROJECT is unset")
        return 2
    print(f"PASS [env]      project={s.google_cloud_project}  location={s.vertex_location}")

    creds, source, sa_email = _load_credentials(s)
    print(f"PASS [creds]    source={source}  service_account={sa_email}")

    from google import genai

    client = genai.Client(
        vertexai=True,
        project=s.google_cloud_project,
        location=s.vertex_location,
        credentials=creds,
    )
    print("PASS [client]   genai.Client(vertexai=True) constructed")

    model = "gemini-2.5-flash"
    resp = client.models.generate_content(
        model=model,
        contents="Reply with exactly: OK",
    )
    text = (resp.text or "").strip()
    if not text:
        print(f"FAIL [call]     model={model} returned empty text")
        return 1
    print(f"PASS [call]     model={model}  reply={text!r}")

    print("\nAuth verified end-to-end. AIV-79 smoke complete on this host.")
    print("Re-run on Replit to satisfy the deploy-side acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
