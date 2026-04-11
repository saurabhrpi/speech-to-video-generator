# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says.

## Current Session: 22
**Date:** 2026-04-10
**Branch:** main
**Status:** OAuth login fixed & verified, stale pipeline fix verified, ffmpeg stitch confirmed fast (4s), SSE heartbeat fix applied but untested.

## What Happened This Session
- Fixed mobile OAuth: one-time token exchange pattern bridges browser cookie jar to app's fetch(). Verified working.
- Confirmed stale pipeline state fix works after app rebuild.
- Confirmed ffmpeg stitch blazing fast on Replit (4s). Can unset `STITCH_TMPDIR`.
- Diagnosed SSE stream drops during video gen (60-90s silence kills connection). Added 15s heartbeat + frontend now distinguishes `phase_completed` vs `success:false`. Untested.

## Next Step (ToDo's)
1. **Full pipeline run shows video reviewer screen** — When running normally (without "Step by step generation" option), the app still shows a PipelineReview screen with buttons like "Generate transition 1→2", "Generate Remaining Videos", etc. This should NOT happen — full pipeline should run end-to-end without pausing for review. Root cause: SSE connection drops during long video generation (~60-90s silence). Fix applied: SSE heartbeat + frontend result handling improvements. Needs testing.
2. Parallelize transition I2V generation (`video_service.py:562-664`) — biggest remaining bottleneck.
3. Migrate `expo-av` → `expo-video` (+ `expo-audio` if used). Warning fires every cold start. Package says "removed in SDK 54" — verify actual removal version, may be urgent.
4. Remove "Test SSE (fake job)" button from mobile UI.
5. Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — mini pipeline UX still broken.

## Open Questions
- Bleed audit marks bled elements as "renovated" causing early exit (deferred).
