# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says.
> **V2 backlog:** Interior Timelapse work was archived to `INTERIOR_TIMELAPSE_V2_BACKLOG.md` during the session-24 pivot. Read that when Interior Timelapse work resumes.

## Current Session: 25
**Date:** 2026-04-11
**Branch:** main
**Status:** Speech-to-Video pipeline working end-to-end with SSE streaming. First Hailuo generation succeeded but VideoPlayer timed out loading the video.

## What Happened This Session
- Mobile app now mirrors web pivot: Speech tab is default (renamed files so speech=index.tsx), endpoint updated to `/api/generate/speech-to-video`, textarea + "Generate Video" button above record, model picker (Kling/Hailuo) + duration picker (Kling: 3/10/15s, Hailuo: 6/10s).
- Backend accepts `model` and `duration` form params. Added `hailuo_t2v_model` to config.
- Converted speech-to-video from synchronous POST (caused 504 timeouts) to job-based SSE streaming via existing `/api/jobs/{job_id}/stream` infrastructure.
- Discovered `RUN_STARTUP_DIAGNOSTIC` was silently draining AIMLAPI credits on every Replit container restart (~hourly). User deleted the secret.
- NativeWind dynamic className on Pressable caused render crashes; fixed by using inline `style` for conditional active/inactive states.
- VideoPlayer load timeout bumped from 15s to 30s (not yet pushed/tested).

## Next Step (ToDo's)
1. **Debug VideoPlayer timeout:** First generation returned "Done!" but player showed "Video timed out — could not load." Check Replit logs for the actual video_url returned. Determine if it's a bad URL, slow CDN, or timeout too short. The 30s timeout fix is local but not pushed yet.
2. **Delete `RUN_STARTUP_DIAGNOSTIC` from Replit Secrets** — user may have done this already, confirm.
3. Re-test with Kling model (only Hailuo tested so far).
4. Test the recorded-audio path (only typed-prompt tested so far).
5. **If simulator paste breaks again:** Toggle Edit > "Automatically Sync Pasteboard" off/on in Simulator menu. Fallback: add `alias simpaste='pbpaste | xcrun simctl pbcopy booted'` to `~/.zshrc`, then just run `simpaste`.

## Open Questions
- What video_url did the successful Hailuo generation return? Need Replit logs to diagnose the player timeout.
- Is 30s enough for VideoPlayer, or is the URL itself bad?
- Is the simulator paste issue sorted permanently (after `defaults write` fix), or will it need `pbpaste | xcrun simctl pbcopy booted` every time?
