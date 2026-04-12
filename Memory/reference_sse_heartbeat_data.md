---
name: SSE heartbeats must be real data events
description: SSE needs heartbeats every ~10s (video gen can stall for minutes with no status change), and they must be real "data:" events not comments
type: reference
---

Two separate lessons about SSE heartbeats:

**1. Heartbeats are mandatory.** Video generation can go minutes with no status change (e.g., waiting for AIMLAPI to finish a single clip). Without heartbeats, the connection sits idle and the reverse proxy (Replit, Cloudflare) kills it after its timeout (~60-90s). SSE must send heartbeats every ~10s regardless of whether state changed.

**2. Heartbeats must be real `data:` events, not comments.** SSE comment-style heartbeats (`: ping\n\n`) get silently dropped by reverse proxies — they don't count as "data flowing." Use real `data:` events that re-send the current job state. The client treats identical state as a no-op.

Implemented in `/api/jobs/{job_id}/stream` — polls every 0.5s, re-sends state as `data:` after 20 idle polls (10s). Client-side `streamJob` in `mobile/lib/streaming.ts` also auto-reconnects (up to 20 retries, 2s delay) as a fallback.
