# Session Log

## Current Session: 19
**Date:** 2026-04-06
**Branch:** main
**Status:** SSE working end-to-end (verified via fake job); i2v_duration crash fixed; mini pipeline available.

## What Happened This Session
- Replaced polling with SSE (`/api/jobs/{id}/stream`) — backend pushes state diffs, frontend uses `expo/fetch` (built-in RN fetch has no streaming body)
- Added file logging via RotatingFileHandler so Replit logs are retrievable via git
- Added fake job endpoint (`/api/debug/fake-job`) for $0 SSE testing + mini pipeline (`num_stages=2`) for cheap real testing
- Fixed pre-existing `UnboundLocalError: i2v_duration` — moved i2v_model/resolution/duration outside the `if start_idx < total_transitions` block so the final pan path can see them
- Fixed `lib/` gitignore rule that was hiding `mobile/lib/streaming.ts`

## Next Step
1. Address the biggest issue - "Stitching remains the bottleneck" : For the mini-pipeline, 120 frames took 25 mins to finish stitching with SSE implemented. So, SSE was not able to cut down the stitching time. What next? 
2. User to choose: (a) commit i2v_duration fix only, (b) also fix frontend `NUM_STAGES = 7` hardcoded so mini pipeline UX is correct, (c) also clean up redundant i2v_model/i2v_resolution defs in final pan block
3. Parallelize transition video generation — all I2V calls are independent (image pair i→i+1 has no dependency on pair j→j+1). Fire them concurrently with `asyncio.gather` or `ThreadPoolExecutor` instead of the current sequential loop in `video_service.py:562-664`. Expected to cut video phase from ~N×polling_time to ~1×polling_time.
4. Test tap-to-copy on keyframe images; remove leftover Capacitor files; delete `mobile/assets/Test_Video.mp4`
5. Implement design system from `design/DESIGN_SYSTEM_PRD.md`

## Open Questions
- Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — does num_stages need to flow back into pipelineState so the review UI matches?
- Auth cookie extraction: will expo-web-browser's ASWebAuthenticationSession share cookies with fetch?
- Bleed audit marks bled elements as "renovated" causing early exit (fix deferred — feature-level)
- expo-av deprecated in SDK 54, removed in SDK 55 — plan migration to expo-video
