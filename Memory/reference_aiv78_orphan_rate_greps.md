---
name: aiv-78-orphan-rate-greps
description: How to read AIV-78 lightweight observability log lines to measure V2 job-manager orphan rate from Replit prod logs
metadata:
  type: reference
---

AIV-78 (S64) ships lightweight observability instead of full Firestore-backed
job durability. The job manager is still in-memory (`utils/job_manager.py`),
but three grep-able log lines now let us measure orphan rate from prod logs
and decide whether to escalate to a persistent store post-launch.

## Log tags (all in `src/speech_to_video/api/server.py`)

| Tag | When | Severity | Source |
|---|---|---|---|
| `JOB_MANAGER_STARTUP` | uvicorn startup | INFO | `@app.on_event("startup")` `_log_job_manager_startup` |
| `JOB_ORPHAN_SNAPSHOT` + `JOB_ORPHAN` | uvicorn shutdown (graceful SIGTERM only) | INFO/WARN | `@app.on_event("shutdown")` `_log_job_orphan_snapshot` |
| `JOB_POLL_MISS` | mobile polls a `job_id` not in `_jobs` | WARN | `get_job_status` 404 branch |

Each line is `key=value` formatted for grep stability.

## Grep recipes

```bash
# Restart count over a window
grep "JOB_MANAGER_STARTUP" prod.log | wc -l

# Orphaned jobs at graceful shutdown (does NOT catch hard SIGKILL restarts)
grep "JOB_ORPHAN " prod.log | wc -l

# User-perceived orphans — INCLUDES hard-kill cases that miss the shutdown hook
grep "JOB_POLL_MISS" prod.log | wc -l

# Orphans by uid (useful if a specific user is hitting it repeatedly)
grep "JOB_POLL_MISS" prod.log | sed 's/.*uid=\([^ ]*\).*/\1/' | sort | uniq -c | sort -rn
```

**Orphan rate** = `JOB_POLL_MISS / total_jobs_submitted` over a comparable window.

## Decision rule (locked S64 with AIV-78)

- **Orphan rate >1-2% first week of V2 prod:** escalate to option C — Firestore-backed
  job store, mirror `credit_store` pattern. AIV-78 Linear ticket describes the
  approach in §Options #1.
- **Orphan rate <1%:** AIV-78 stays as accepted-risk. Lightweight observability
  remains for ongoing visibility.

## Pitfalls when reading these logs

- **Replit container restarts vs. graceful redeploys.** Graceful redeploys (e.g.
  `replit deploy` rollout) fire `JOB_ORPHAN_SNAPSHOT`. SIGKILL crashes do NOT.
  Always cross-reference with `JOB_MANAGER_STARTUP` to count actual restart
  events.
- **`JOB_POLL_MISS` also fires for stale 1-hour TTL evictions**, not just
  container-restart orphans. Distinguish by: if the job's submit log appears
  AFTER the most recent `JOB_MANAGER_STARTUP` but a `POLL_MISS` follows within
  the TTL window, it's a true restart-orphan, not TTL eviction.
- **Job credit_cost is logged in `JOB_ORPHAN` lines** — multiply by orphan count
  to estimate $ wasted on Kling/Vertex/etc. for which we never charged the
  user (their grant is gated on completion via `_maybe_consume_job_credits`).

## Cross-references

- `reference_replit_workspace_vs_deployment_secrets.md` — Replit deploy quirks
- `reference_replit_startup_event.md` — Replit container-restart frequency
