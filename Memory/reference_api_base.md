---
name: Deployed backend API base URLs
description: Production backend URLs for the FastAPI server. Two hostnames both hit the same Replit deployment — use the .ai canonical domain for anything user-facing or mobile-config-aligned, .replit.app is fine for ad-hoc curls.
type: reference
---

**Canonical (user's purchased domain, what mobile uses):** `https://speech-2-video.ai`
**Underlying Replit host (alias):** `https://speech-to-video-generator.replit.app`

Both resolve to the same FastAPI app (`src/speech_to_video/api/server.py`). Mobile sets `API_BASE = 'https://speech-2-video.ai'` in `mobile/lib/constants.ts`.

**Useful one-liners:**

```bash
# Health
curl -sS https://speech-2-video.ai/api/health

# Setup / env-flag inspection
curl -sS https://speech-2-video.ai/api/setup

# Route fingerprint — does endpoint exist post-deploy?
curl -sS -o /dev/null -w "%{http_code}\n" -X DELETE https://speech-2-video.ai/api/account
# 401 = route registered + auth dep rejected empty header (expected)
# 404 / 405 = deploy is stale, mobile tests will lie
```

Per `feedback_verify_deploy_before_integration_test.md`, always fingerprint before mobile integration testing if the change touched backend code.
