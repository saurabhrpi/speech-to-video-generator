---
name: kling-task-hang-detection
description: Kling Motion Control tasks can hang silently with task_status="processing" and no updated_at progress. Direct-poll to verify; no credits are charged for hung tasks. Our client's max_wait=600s caps the wait, but doesn't auto-retry.
metadata:
  type: reference
---

**Failure mode:** Kling tasks sometimes hang at `task_status: "processing"` with no `updated_at` movement past the initial submit. Healthy gens complete in 4-6 min with progressive `updated_at` updates; hung ones sit with `updated_at` frozen 10-30s after `created_at` indefinitely.

**Diagnostic (one-liner):**
```python
from speech_to_video.clients.kling_motion_client import KlingMotionClient
import requests, datetime, json
c = KlingMotionClient()
url = f'{c.base_url}/v1/videos/motion-control/{TASK_ID}'
r = requests.get(url, headers=c._headers(), timeout=30)
d = r.json().get('data', {})
print(f'status: {d.get("task_status")}')
print(f'created: {datetime.datetime.fromtimestamp(d.get("created_at", 0)/1000)}')
print(f'updated: {datetime.datetime.fromtimestamp(d.get("updated_at", 0)/1000)}')
```

**Hung if:** `updated_at - created_at < 60s` AND wall-clock since `created_at` > 5x typical gen time (i.e., ~20-30 min on a normally 4-6 min gen).

**No credits charged for hung tasks** (user-verified S72 on the Kling console — hung Thriller task `886680218651066459` did not appear in billing).

**Our client's behavior on timeout:** `KlingMotionClient.generate_and_poll(max_wait=600)` returns `{"success": False, "error": "Generation timed out"}` after 10 min. Job manager treats this as a failure; `_maybe_consume_job_credits` does NOT consume credits on failure. So our credit ledger matches Kling's billing — no double-charge risk.

**Mid-poll network errors mask hangs:** if the poll loop hits read-timeouts or DNS errors while the gen is hung, our log shows those errors first (which look like client problems). Always direct-poll once to disambiguate before re-submitting.

**Production resilience gap (V2.0.2 candidates):**
- No auto-retry on Kling timeout — user has to manually re-tap "generate" today
- No "still working" UI past 5 min — generic progress copy
- No explicit apology + "no credits charged" CTA on failure

**How to apply:** when a Kling chain script's `generate_and_poll` reports timeout, ALWAYS direct-poll the task_id once before re-submitting — the task may still be processing (rare) or hung (common). Re-submitting is safe (no credit risk) but wasteful if the original is still going.

**S83 push-style monitor + false-positive lesson:** `scripts/monitor_kling_task.py` polls Kling in the background and exits on terminal state, decoupling polling from the foreground conversation (submit-only inline + background monitor). It exits with code 0/1/2/3 (succeed / failed / hung / timeout). Its **hang detection (300s without `updated_at` movement) gives false positives** on slow-but-alive tasks — Got 2 Luv U v3 monitor declared hung at exit code 2, but a direct poll right after showed `task_status: succeed`. So the workflow rule is **HARD: always direct-poll once before treating a monitor's HUNG exit (code 2) as truly hung.** Triggered ONLY after 300s of no monitor updates (the natural moment the monitor exits hung) — don't poll externally any earlier (S83 user-locked rule). True hangs in S83 sat in `task_status: "submitted"` for >5 min (Kling never picked them up); false-positive hangs sat in `task_status: "processing"`. Track that discriminator when triaging.
