"""Smoke test for AIV-82 — set_status + template_status_log audit chain.

Touches real Firestore. Seeds `smoketest-aiv-82` as draft, flips through three
status transitions with different actors/reasons/uids, asserts the audit log
records each flip in order, then cleans up doc + log entries.

Coverage:
- Each set_status call writes one log entry (batched with doc update).
- from_status chains correctly across calls.
- actor/uid/reason fields persist.
- list_status_log(template_id=...) returns entries newest-first.
- Bad status -> ValueError. Missing template -> TemplateNotFound.

Usage:
    .venv/bin/python scripts/test_template_status_log.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore")

from src.speech_to_video.utils import template_registry as tr  # noqa: E402


SMOKE_ID = "smoketest-aiv-82"
SMOKE_DOC = {
    "pipeline_class": tr.PIPELINE_MOTION_TRANSFER,
    "outcome": tr.OUTCOME_ONTO_CHARACTER,
    "category": "smoketest",
    "title": "AIV-82 Smoke",
    "description": "Smoke fixture for set_status audit log.",
    "published_status": tr.STATUS_DRAFT,
    "assets": {
        "driving_video_url": "https://placeholder.example/smoke.mp4",
        "scene_image_url": None,
        "thumbnail_url": None,
        "preview_video_url": None,
    },
    "model": "kling-2.6-motion-control-image",
    "credit_cost": 23,
    "prompt_template": None,
}


def main() -> int:
    # Always start clean — previous failed runs may have left state.
    tr._delete_status_log_for(SMOKE_ID)
    try:
        tr.delete_template(SMOKE_ID)
    except Exception:
        pass

    tr.upsert_template(SMOKE_ID, SMOKE_DOC)

    try:
        # 1. draft -> qa-pending via CLI
        after = tr.set_status(SMOKE_ID, tr.STATUS_QA_PENDING, actor="cli")
        assert after["published_status"] == "qa-pending", f"flip 1: {after['published_status']}"
        print(f"PASS  flip 1      draft -> qa-pending (actor=cli)")

        # 2. qa-pending -> published via auto-pause with reason
        after = tr.set_status(
            SMOKE_ID,
            tr.STATUS_PUBLISHED,
            actor="auto-pause",
            reason="user_flag_threshold_0.3",
        )
        assert after["published_status"] == "published", f"flip 2: {after['published_status']}"
        print(f"PASS  flip 2      qa-pending -> published (actor=auto-pause, reason=...)")

        # 3. published -> draft via admin with uid
        after = tr.set_status(
            SMOKE_ID,
            tr.STATUS_DRAFT,
            actor="admin",
            uid="test-admin-uid",
        )
        assert after["published_status"] == "draft", f"flip 3: {after['published_status']}"
        print(f"PASS  flip 3      published -> draft (actor=admin, uid=...)")

        # 4. Audit log: 3 entries, newest-first, chained from/to.
        logs = tr.list_status_log(template_id=SMOKE_ID)
        assert len(logs) == 3, f"expected 3 log entries, got {len(logs)}"
        # Newest first: flip 3, flip 2, flip 1.
        assert logs[0]["to_status"] == "draft" and logs[0]["from_status"] == "published"
        assert logs[0]["actor"] == "admin" and logs[0]["uid"] == "test-admin-uid"
        assert logs[0]["reason"] is None

        assert logs[1]["to_status"] == "published" and logs[1]["from_status"] == "qa-pending"
        assert logs[1]["actor"] == "auto-pause"
        assert logs[1]["reason"] == "user_flag_threshold_0.3"
        assert logs[1]["uid"] is None

        assert logs[2]["to_status"] == "qa-pending" and logs[2]["from_status"] == "draft"
        assert logs[2]["actor"] == "cli"
        assert logs[2]["reason"] is None and logs[2]["uid"] is None

        # Each entry has a server timestamp and a doc id.
        for entry in logs:
            assert entry.get("ts") is not None, f"log entry missing ts: {entry}"
            assert entry.get("id"), f"log entry missing doc id: {entry}"
            assert entry["template_id"] == SMOKE_ID
        print(f"PASS  audit log   3 entries chained, newest-first, fields persisted")

        # 5. Bad status -> ValueError, no log entry written.
        baseline_count = len(tr.list_status_log(template_id=SMOKE_ID))
        try:
            tr.set_status(SMOKE_ID, "invalid-status-zzz")
        except ValueError:
            pass
        else:
            raise AssertionError("bad status should have raised ValueError")
        assert len(tr.list_status_log(template_id=SMOKE_ID)) == baseline_count, "bad-status flip wrote a log entry"
        print(f"PASS  bad status  ValueError raised, no log entry leaked")

        # 6. Missing template -> TemplateNotFound, no log entry.
        try:
            tr.set_status("nonexistent-template-zzz", tr.STATUS_PUBLISHED)
        except tr.TemplateNotFound:
            pass
        else:
            raise AssertionError("missing template should have raised TemplateNotFound")
        # Across-all log query shouldn't have a new entry for the bogus id.
        bogus_logs = tr.list_status_log(template_id="nonexistent-template-zzz")
        assert len(bogus_logs) == 0, f"missing template wrote a log entry: {bogus_logs}"
        print(f"PASS  missing tpl TemplateNotFound, no log entry")

        print("\nAll AIV-82 audit log smokes passed.")
        return 0
    finally:
        tr._delete_status_log_for(SMOKE_ID)
        tr.delete_template(SMOKE_ID)


if __name__ == "__main__":
    raise SystemExit(main())
