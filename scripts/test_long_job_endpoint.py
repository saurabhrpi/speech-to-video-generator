"""Smoke test for the AIV-80 long-job thread-durability harness.

Launches a short (60s by default) long-job against a locally-running uvicorn
instance, polls every 10s, and asserts the worker thread completes cleanly
(status transitions queued -> running -> completed; final result populated;
no intermediate errors).

This is the *local* verification that the harness itself works. The actual
AIV-80 verification — Replit doesn't kill 7-8min worker threads — must run
against Replit prod with duration_s=480 (see procedure block in
src/speech_to_video/api/server.py near `/api/debug/long-job`).

Prerequisites:
    ENABLE_LONG_JOB_TEST=1 .venv/bin/python -m uvicorn \\
        src.speech_to_video.api.server:app --host 0.0.0.0 --port 5000

Then in another shell:
    .venv/bin/python scripts/test_long_job_endpoint.py
"""
from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("test_long_job_endpoint")

BASE = os.environ.get("API_BASE", "http://127.0.0.1:5000").rstrip("/")
DURATION_S = int(os.environ.get("DURATION_S", "60"))
POLL_EVERY_S = int(os.environ.get("POLL_EVERY_S", "10"))


def main() -> int:
    log.info("base=%s duration_s=%s poll_every_s=%s", BASE, DURATION_S, POLL_EVERY_S)

    try:
        r = requests.post(f"{BASE}/api/debug/long-job", params={"duration_s": DURATION_S}, timeout=10)
    except requests.exceptions.ConnectionError as e:
        log.error("connection refused — is uvicorn running on %s?\n%s", BASE, e)
        return 2

    if r.status_code == 404 and "disabled" in r.text:
        log.error("endpoint disabled — start uvicorn with ENABLE_LONG_JOB_TEST=1")
        return 2
    if not r.ok:
        log.error("start failed: %s %s", r.status_code, r.text)
        return 3

    body = r.json()
    job_id = body["job_id"]
    poll_url = f"{BASE}{body['poll_url']}"
    log.info("PASS [start]         job_id=%s tick_s=%s", job_id, body["tick_s"])

    deadline = time.time() + DURATION_S + 30  # generous safety
    last_status = None
    poll_failures = 0
    saw_running = False

    while time.time() < deadline:
        try:
            r = requests.get(poll_url, timeout=5)
        except requests.exceptions.RequestException as e:
            poll_failures += 1
            log.warning("poll exception: %s", e)
            time.sleep(POLL_EVERY_S)
            continue

        if not r.ok:
            poll_failures += 1
            log.warning("poll non-200: %s %s", r.status_code, r.text)
            time.sleep(POLL_EVERY_S)
            continue

        body = r.json()
        status = body.get("status")
        if status != last_status:
            log.info("  status=%s phase=%s step=%s/%s msg=%r",
                     status, body.get("phase"), body.get("step"),
                     body.get("total_steps"), body.get("message"))
            last_status = status
        if status == "running":
            saw_running = True
        if status == "completed":
            assert saw_running, "never observed status=running before completed"
            result = body.get("result") or {}
            assert result.get("success") is True, f"expected success=true, got {result}"
            assert result.get("video_url") == "debug://aiv-80", f"unexpected video_url: {result}"
            log.info("PASS [completed]     final result=%s", result)
            log.info("PASS [poll-health]   poll_failures=%d (over %ds)", poll_failures, DURATION_S)
            if poll_failures > 0:
                log.warning("note: %d poll failures observed", poll_failures)
            return 0
        if status == "failed":
            log.error("worker failed: %s", body)
            return 4

        time.sleep(POLL_EVERY_S)

    log.error("timeout: job did not reach completed within %ds", DURATION_S + 30)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
