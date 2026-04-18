# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 36
**Date:** 2026-04-18
**Branch:** main
**Status:** Backend Firebase migration DONE (Task 8 ✓). Local smoke tests pass. Next: Replit deploy + EAS build.

## What Happened This Session
- Rewrote `src/speech_to_video/api/server.py`: removed authlib/SessionMiddleware/OAuth routes, every protected endpoint now takes `Depends(verify_firebase_token)`, usage gating switched to per-UID dict (anon-only), clip namespace keyed on Firebase UID, jobs track `uid`/`is_anonymous` so usage counts only on anon completion.
- New `src/speech_to_video/api/firebase_auth.py` — lazy-inits firebase-admin from `FIREBASE_SERVICE_ACCOUNT_PATH` (expands `~`), maps expired/revoked/invalid to 401.
- `requirements.txt`: `firebase-admin>=6.5.0` in; `authlib`/`itsdangerous` out. `.env` cleaned of Google/session vars; `FIREBASE_SERVICE_ACCOUNT_PATH=~/secrets/speech-to-video-97e43-firebase-adminsdk-fbsvc-50e5f7a650.json`.
- Smoke test live: `/api/health` 200; `/api/auth/session` 401 no-token and 401 bad-token (proves firebase-admin initialized).
- [AUTH_MIGRATION.md](AUTH_MIGRATION.md) Task 9/10 rewritten — Task 9 now three phases (local smoke → Replit deploy → EAS). Task 10 adds pre-submission gate + 5.1.1(v) account-deletion risk.

## Next Step
Task #9 Phase B — deploy backend to Replit. Decision point: how to deliver the service account JSON to Replit (file-secret vs. `FIREBASE_SERVICE_ACCOUNT_JSON` string env var with small code change). Then strip dead Google/session secrets from Replit, push main, verify `/api/health` + `/api/setup` shows `firebase_service_account_present: true`.

## Open Questions
- Replit service-account file delivery mechanism (file-secret feature availability on current tier)
- Account deletion UI (Apple 5.1.1(v)) — deferred, ship without and see if reviewer flags
- 4.3a carryover risk still outstanding for Task 10
