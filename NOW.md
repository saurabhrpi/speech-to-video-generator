# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 33
**Date:** 2026-04-15
**Branch:** main
**Status:** EAS version bump fixed. Session-loss-after-a-day investigation UNRESOLVED — many hypotheses eliminated, two suspects still open.

## What Happened This Session
- Fixed EAS versioning: switched `mobile/eas.json` to `appVersionSource: "local"` + `autoIncrement: "version"`. Next build will be 1.0.1, then 1.0.2, etc. (no more `1.0.0(2)` build numbers).
- Investigated "sign in required after a day" issue. Confirmed via curl + local server + simulator debug logs:
  - Server sets `session` cookie with `Max-Age=2592000` (30d) ✓
  - Google Frontend does NOT strip it ✓
  - RN fetch CAN read `Set-Cookie` (my earlier hypothesis was wrong) ✓
  - Cookie IS stored in SecureStore, sent, and refreshed in simulator ✓
- Got course-corrected: user reminded me the "one free trial" flow is baked in via `UNAUTH_GEN_LIMIT=1` (documented in CLAUDE.md). Symptom = server treating returning user as brand-new unauth visitor.
- Debug logs added to `mobile/lib/api-client.ts` then reverted.

## Next Step
Continue cookie-loss investigation. Two suspects left:
1. `extractAndStoreCookie` uses `split(';')[0]` — if GAESA ever appears first in concatenated Set-Cookie, we overwrite the real session cookie with GAESA. Test: hit production endpoints, inspect order of Set-Cookie headers, see if GAESA can ever come first.
2. `SESSION_SECRET` mismatch: user's Replit secret is named `Session_Secret` (mixed case); code reads `os.getenv("SESSION_SECRET")` (uppercase). On Linux env vars are case-sensitive, so code falls back to `"change-me"`. Stable default shouldn't cause day-1 invalidation, but worth verifying what the server actually uses.

## Open Questions
- Why does the server see the user as unauthenticated after ~1 day, when the cookie appears to work correctly in simulator tests?
- Was my curl-to-production attempt rejected because of an active generation, or for another reason?
- Session-31 red-line-at-top observation when FaceTime ended — still unresolved, still low-priority.
