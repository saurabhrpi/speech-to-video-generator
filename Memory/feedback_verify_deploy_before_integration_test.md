---
name: Verify backend deploy before mobile integration test
description: Before testing a mobile UI change that assumes new backend endpoints or response fields, confirm the backend changes are committed AND deployed on the target — otherwise the test result is meaningless and will masquerade as a mobile bug
type: feedback
---

When a mobile change depends on new backend behavior (new endpoint, new response field, new gate semantics), the integration test is only meaningful if the production backend actually has those changes. Running it against stale production produces results that look like mobile bugs but are really "the server you're talking to is the wrong version."

**Why (Session 47 incident):** Session 46 refactored both backend (new `credit_store.py` / `credits.py` / updated `/api/auth/session` + `/api/generate/speech-to-video` credit gate) and mobile (credit-aware paywall + button cost label) in the same session. Session 47 `/wake` skipped `git status`, assumed the backend was deployed, and ran a fresh-install simulator test against `speech-2-video.ai`. The 2nd Hailuo gen came back `401 login_required` — the OLD anon gate from HEAD `2bb9a1d`. All 5 backend files were still uncommitted in the working tree. Mobile was new; server was old; they disagreed; I spent ~20 minutes diagnosing what looked like a product bug.

**How to apply:**
- At `/wake` for any session that follows one with mobile+backend changes, run `git status` first — uncommitted server code is a red flag for "production doesn't have this yet."
- Before an integration test, curl a fingerprint on the deploy target that only exists in the new code — a new endpoint (expect 401/200 vs 404), a new response field, or a renamed error detail. Example: `curl -s -o /dev/null -w '%{http_code}' -X POST https://host/api/credits/grant` → 404 means the router isn't mounted; 401/405 means it is.
- If the fingerprint says production is stale, either deploy first or explicitly mark the test as blocked. Don't diagnose a mobile UI against the wrong server.
- Applies to any deploy target, not just Replit — same logic for staging, preview, or a teammate's branch deploy.
