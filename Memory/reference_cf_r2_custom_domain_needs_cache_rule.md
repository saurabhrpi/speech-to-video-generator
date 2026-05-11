---
name: CF R2 custom domain needs explicit Cache Rule for edge caching
description: Cloudflare R2 custom-domain hostnames are proxied through CF's edge but do NOT auto-cache responses. A Cache Rule must be added explicitly; without it CF-Cache-Status returns DYNAMIC and origin Cache-Control headers are honored only by browsers, not by the CF edge.
type: reference
---

After binding `assets.speech-2-video.ai` to an R2 bucket via the CF dashboard, fetches through the custom domain returned `CF-Cache-Status: DYNAMIC` — meaning CF didn't even attempt to cache, despite the response carrying `Cache-Control: public, max-age=31536000, immutable`.

**Fix:** Add a Cache Rule explicitly in the CF zone:
- Zone → Caching → Cache Rules → Create rule
- When incoming requests match: Hostname equals `<r2-custom-domain>`
- Then (Cache settings): Eligible for cache + Edge TTL: "Use cache-control header if present, use default Cloudflare caching behavior if not"
- Deploy

Within ~10 seconds of deployment, subsequent fetches show `CF-Cache-Status: HIT` (after one warming `MISS` for cold edge cache).

**Why it's not on by default:** CF treats R2 custom domain hostnames as transparent proxies unless told otherwise — likely to avoid surprising customers who want raw-pass-through. Browser-level `Cache-Control` honoring still works (clients cache locally) but you lose the global edge cache benefit until the rule is in place.

**Verified S61 (2026-05-10).** Smoke test went from `CF-Cache-Status: DYNAMIC` to `HIT` immediately after the Cache Rule was deployed. Smoke test is at `scripts/test_r2_client.py`.
