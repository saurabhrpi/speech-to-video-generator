"""Smoke test for AIV-83 — GET /api/templates.

Uses FastAPI TestClient (in-process, no server boot). Touches real Firestore:
seeds a dedicated `smoketest-aiv-83-published` doc and deletes it at the end.
Bombale is `draft`, so this won't mutate it.

Coverage:
- 200 + ETag + Cache-Control + seeded template present (timestamps ISO)
- 304 on matching If-None-Match (no body, ETag echoed)
- 200 on mismatched If-None-Match (re-fetched)
- In-process cache: 4 GETs within TTL → 1 list_templates() call

Usage:
    .venv/bin/python scripts/test_templates_endpoint.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from src.speech_to_video.api import server as server_mod  # noqa: E402
from src.speech_to_video.utils import template_registry  # noqa: E402


SMOKE_ID = "smoketest-aiv-83-published"
SMOKE_DOC = {
    "pipeline_class": template_registry.PIPELINE_MOTION_TRANSFER,
    "outcome": template_registry.OUTCOME_ONTO_CHARACTER,
    "category": "smoketest",
    "title": "AIV-83 Smoke",
    "description": "Smoke fixture for GET /api/templates.",
    "published_status": template_registry.STATUS_PUBLISHED,
    "assets": {
        "driving_video_url": "https://placeholder.example/smoke-driving.mp4",
        "scene_image_url": None,
        "thumbnail_url": "https://placeholder.example/smoke-thumb.jpg",
        "preview_video_url": None,
    },
    "model": "kling-2.6-motion-control-image",
    "credit_cost": 23,
    "prompt_template": None,
}


def _reset_cache():
    server_mod._template_cache["ts"] = 0.0
    server_mod._template_cache["templates"] = None
    server_mod._template_cache["etag"] = None


def main():
    template_registry.upsert_template(SMOKE_ID, SMOKE_DOC)
    _reset_cache()
    client = TestClient(server_mod.app)

    try:
        # 1. Happy path — 200 + ETag + seeded template present
        r = client.get("/api/templates")
        assert r.status_code == 200, f"happy: {r.status_code} {r.text}"
        etag = r.headers.get("etag")
        assert etag and etag.startswith('W/"'), f"happy: bad ETag {etag!r}"
        assert r.headers.get("cache-control"), "happy: missing Cache-Control"
        body = r.json()
        assert "templates" in body, f"happy missing templates key: {body}"
        ids = {t["id"] for t in body["templates"]}
        assert SMOKE_ID in ids, f"smoke template missing from list: {ids}"
        tpl = next(t for t in body["templates"] if t["id"] == SMOKE_ID)
        assert tpl["title"] == "AIV-83 Smoke"
        assert tpl["pipeline_class"] == "motion-transfer"
        assert tpl["credit_cost"] == 23
        assert tpl["published_status"] == "published"
        ua = tpl.get("updated_at")
        assert isinstance(ua, str) and "T" in ua, f"updated_at not ISO: {ua!r}"
        print(f"PASS  200 happy    etag={etag} templates={len(body['templates'])}")

        # 2. If-None-Match match → 304, no body, ETag echoed
        r = client.get("/api/templates", headers={"If-None-Match": etag})
        assert r.status_code == 304, f"304: {r.status_code} {r.text}"
        assert r.headers.get("etag") == etag, f"etag drifted: {r.headers.get('etag')}"
        assert not r.content, f"304 body present: {r.content!r}"
        print(f"PASS  304 INM      etag echoed, no body")

        # 3. If-None-Match mismatch → 200
        r = client.get("/api/templates", headers={"If-None-Match": 'W/"deadbeef"'})
        assert r.status_code == 200, f"INM mismatch: {r.status_code} {r.text}"
        print(f"PASS  200 INM-miss refetched")

        # 4. Cache: instrument list_templates and verify TTL-window dedupe.
        original_list = template_registry.list_templates
        call_count = {"n": 0}

        def _counting(*args, **kwargs):
            call_count["n"] += 1
            return original_list(*args, **kwargs)

        template_registry.list_templates = _counting
        try:
            _reset_cache()
            for i in range(4):
                r = client.get("/api/templates")
                assert r.status_code == 200, f"cache iter {i}: {r.status_code}"
            assert call_count["n"] == 1, (
                f"cache leaked: expected 1 Firestore fetch across 4 GETs, got {call_count['n']}"
            )
            print(f"PASS  cache       4 GETs → 1 list_templates() call")
        finally:
            template_registry.list_templates = original_list

        print("\nAll AIV-83 endpoint smokes passed.")
        return 0
    finally:
        template_registry.delete_template(SMOKE_ID)
        _reset_cache()


if __name__ == "__main__":
    raise SystemExit(main())
