---
name: AIMLAPI I2I edit holds connections open
description: AIMLAPI's nano-banana-pro-edit takes ~4:45 end-to-end due to upstream chunked-stream dribble, not our client or network
type: reference
---

AIMLAPI's `google/nano-banana-pro-edit` endpoint deterministically takes ~4:45 per request. The cause is upstream: AIMLAPI sends HTTP headers early (to defeat proxy timeouts) and then holds the chunked response stream open for ~4 more minutes before flushing the 169-byte JSON body.

**Why:** Confirmed 2026-04-11 via a four-probe startup diagnostic on Replit production:
- socket (DNS+TCP+TLS to api.aimlapi.com): 194 ms — network is healthy
- cdn_fetch (1.8 MB png from cdn.aimlapi.com): 1.65 s — CDN is healthy
- t2i (nano-banana-pro, same endpoint/auth): 21.6 s total, TTFB 21.6 s, body 0 ms — fast, normal shape
- **i2i (nano-banana-pro-edit): 287.3 s total, TTFB 51.6 s, body download 235.7 s for a 169-byte response** — anomaly
- Response headers include `Transfer-Encoding: chunked`; `Date` header shows headers arrived ~52 s in, then the connection dribbled for ~4 more min before close.
- Same pattern reproduced in the real pipeline: Stage 3 I2I start→done = 4:45 exactly.
- Rules out: our 2×120 s retry ceiling (single probe, no retries), urllib3 backoff, network, DNS, TLS, CDN, screen sleep, container restart.

**How to apply:**
- When I2I edit is "slow," do NOT theorize about our client, retries, or network — it's AIMLAPI upstream. Don't waste a session re-diagnosing the same thing.
- T2I (`google/nano-banana-pro`) on the same endpoint is fine (~22 s) — don't confuse the two.
- The right mitigation is bypassing AIMLAPI for edits: direct `generativelanguage.googleapis.com` Gemini API, or another reseller.
- If you ever see I2I drop below ~4 min on AIMLAPI, re-verify — it would mean AIMLAPI changed their upstream handling and this memory is stale.
