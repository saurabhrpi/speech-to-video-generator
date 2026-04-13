# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.
> **V2 backlog:** Interior Timelapse work was archived to `INTERIOR_TIMELAPSE_V2_BACKLOG.md` during the session-24 pivot. Read that when Interior Timelapse work resumes.

## Current Session: 28
**Date:** 2026-04-12
**Branch:** main
**Status:** Gallery tab fully implemented and working. AIMLAPI Hailuo unreliable — planning direct MiniMax integration.

## What Happened This Session
- Built Gallery tab (replaced Video Studio) per `design/GALLERY_TAB_PLAN.md`:
  - Gallery store (Zustand): fire-and-forget generation, AbortControllers in module-level Map, keep-awake, AsyncStorage persistence for completed/failed jobs.
  - Speech tab stripped of blocking state — dispatches to gallery store, navigates to Gallery, always interactive.
  - Gallery screen: 2-column FlatList grid (generating=spinner, completed=play+download, failed=error+remove). Tap completed card for full-width VideoPlayer. Save to Camera Roll via `File.downloadFileAsync`.
  - Tab order: Speech, Gallery, Timelapse. Deleted video-studio.tsx.
- Fixed `blob.arrayBuffer()` crash — RN Blob doesn't support it. Used expo-file-system's `File.downloadFileAsync` (new API, not legacy).
- Made failed cards tappable — shows Alert with full error message.
- Added auth session refresh after each generation so `canGenerate()` stays in sync with server usage count.
- Added `hailuo-2.3` and `hailuo-2.3-fast` to backend config. Switched mobile app to `minimax/hailuo-2.3` (T2V). Both Hailuo models timed out on AIMLAPI (stuck in "queued").
- Researched direct MiniMax API — have full endpoint specs ready.

## Next Step (ToDo's)
1. **Build direct MiniMax client.** Bypass AIMLAPI for Hailuo — hit MiniMax API directly. Three-step flow:
   - Submit: `POST https://api.minimax.io/v1/video_generation` (model, prompt, duration, resolution) → `task_id`
   - Poll: `GET https://api.minimax.io/v1/query/video_generation?task_id=...` → statuses: Preparing, Queueing, Processing, Success, Fail → on Success returns `file_id`
   - Download: `GET https://api.minimax.io/v1/files/retrieve?file_id=...` → `download_url` (expires 1h)
   - Auth: Bearer token via `MINIMAX_API_KEY` env var.
   - Model names differ from AIMLAPI: `MiniMax-Hailuo-2.3`, `MiniMax-Hailuo-02`.
   - Docs at `docs/Hailuo_Direct.txt`. Full API reference at `docs/Hailuo_T2V.txt`.
2. Re-test with Kling model (only Hailuo tested so far).
3. Test the recorded-audio path (only typed-prompt tested so far).
4. **Simulator paste keeps breaking.** `simpaste` alias is a workaround, not a fix. Find a permanent solution.

## Open Questions
- Will video URLs from CDN expire after app restart? Gallery persists URLs in AsyncStorage but they may 404. Save-to-device is the permanent solution.
- MiniMax download_url expires after 1 hour — need to either save to device promptly or re-fetch file_id on playback.
