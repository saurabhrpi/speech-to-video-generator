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
