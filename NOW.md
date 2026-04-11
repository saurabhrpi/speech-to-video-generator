# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says.
> **V2 backlog:** Interior Timelapse work was archived to `INTERIOR_TIMELAPSE_V2_BACKLOG.md` during the session-24 pivot. Read that when Interior Timelapse work resumes.

## Current Session: 24
**Date:** 2026-04-11
**Branch:** main
**Status:** PIVOT — Speech to Video is now the MVP/V1. Interior Timelapse demoted to V2. Backend + frontend rewired to Kling T2V. Builds green. Not yet end-to-end tested against real Kling.

## What Happened This Session
- Killed Sora-2 / superbowl code path. New method `VideoService.generate_speech_to_video(text)` — single 10s clip via Kling T2V (`klingai/video-v3-standard-text-to-video`), `generate_audio=False`.
- New endpoint `POST /api/generate/speech-to-video` replaces `/api/ads/superbowl`. Dropped `AD_*` env vars and `ad_seed`/`ad_prev_text` session state.
- Deleted orphans: `generate_16s_video`, `generate_superbowl_ad`, `_superbowl_prompt`, `split_prompt_for_two_clips`. Verified zero references anywhere (Interior Timelapse pipeline untouched).
- Added `kling_t2v_model` to config; extended `AIMLAPIClient.generate_video()` with `generate_audio` kwarg.
- Frontend: tab order now **Speech → Interior Timelapse → Video Studio**, default `mode='speech'`. Added `<textarea>` + "Generate Video" button above the Record path. Renamed `handlePromptToAd` → `handleTextToVideo`. Both paths POST to new endpoint. `py_compile` + `npm run build` both green.
- Kling T2V spec saved at `docs/Kling_T2V.txt`.

## Next Step (ToDo's)
1. **E2E test the pivot:** run server, hit `/api/generate/speech-to-video` from the Speech tab with (a) typed prompt (b) recorded audio. Watch Kling T2V response land. First real validation of the new code path.
2. **Delete `RUN_STARTUP_DIAGNOSTIC` from Replit Secrets** — still pending from the pre-pivot diagnostic work. Burns ~$0.39/boot until removed.
3. Deploy the pivot to Replit after local E2E passes.
4. Decide: does "convert the video into a timelapse" (prompt engineering or ffmpeg speed-up) come back for V1.1, or stay deferred to V2?
5. V2 backlog (Interior Timelapse direct-Gemini I2I, parallel I2V, etc.) lives in `INTERIOR_TIMELAPSE_V2_BACKLOG.md` — do not work on unless explicitly re-prioritized.

## Open Questions
- Does Kling T2V reject `seed` if passed? Not listed in docs — currently not sent. Will learn from first E2E run.
- Does the 10s Kling generation land within the 120s frontend progress budget, or do we need to widen `expectedMs`? Unknown until tested.
