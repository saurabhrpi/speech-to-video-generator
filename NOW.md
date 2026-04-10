# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says.

## Current Session: 21
**Date:** 2026-04-09
**Branch:** main
**Status:** Added ffmpeg stitch logging, fixed stale pipeline state in mobile store, diagnosed OAuth login failure.

## What Happened This Session
- Added `logger.info` timing for ffmpeg stitch start/completion/failure (`video.py`). Logs confirmed full pipeline works: transition 88s, final pan 78s, stitch 1.9s.
- Fixed stale state leaking across pipeline runs in `pipeline-store.ts` — `runPipeline` now clears `videoUrl`/`pipelineState`/`jsonOut`; `videoUrl` branch clears `phaseCompleted`. Error card no longer requires `pipelineState`. Changes need app rebuild to verify.
- Diagnosed mobile OAuth login broken: browser cookie jar (ASWebAuthenticationSession) separate from app's SecureStore. No code changed since it last worked (~Apr 6).

## Next Step (ToDo's)
1. **Fix Google OAuth login on mobile** — Login flow completes in browser but app doesn't get the session cookie. The browser's cookie jar (ASWebAuthenticationSession) is separate from the app's `fetch()` (which uses manual cookie management via SecureStore). Need to bridge this gap — likely by passing a one-time token in the deep link redirect and adding an `/api/auth/exchange` endpoint so the app can obtain the cookie directly. Was working ~Apr 6, stopped without code changes — investigate what changed (iOS cookie sharing behavior? simulator reset?). Files: `mobile/lib/auth.ts`, `server.py:163-188`.
2. **Fix stale pipeline state leaking across runs** — `runPipeline` in `pipeline-store.ts` doesn't clear `videoUrl`, `pipelineState`, or `jsonOut` at start. Old video/state bleeds into new runs (confirmed: 401 error showed stale video from previous mini pipeline). Also: `videoUrl` branch should explicitly clear `phaseCompleted` to prevent both PipelineReview and VideoPlayer rendering. Partially fixed in this session — changes in `pipeline-store.ts:56-64` and `pipeline-store.ts:108-115`, plus error card condition in `index.tsx:130`. Need to rebuild app to verify.
3. **Test ffmpeg stitch on Replit** — push, run a full timelapse, confirm it works on plain `/tmp` without `STITCH_TMPDIR`. Then unset `STITCH_TMPDIR` from Replit Secrets.
4. Parallelize transition I2V generation (`video_service.py:562-664`) — biggest remaining bottleneck.
5. Migrate `expo-av` → `expo-video` (+ `expo-audio` if used). Warning fires every cold start. Package says "removed in SDK 54" — verify actual removal version, may be urgent.
6. Remove "Test SSE (fake job)" button from mobile UI.
7. Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — mini pipeline UX still broken.

## Open Questions
- Bleed audit marks bled elements as "renovated" causing early exit (deferred).
