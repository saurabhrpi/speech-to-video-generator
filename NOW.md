# Session Log

## Current Session: 18
**Date:** 2026-04-06
**Branch:** main
**Status:** VideoPlayer tested and hardened with load timeout.

## What Happened This Session
- Tested VideoPlayer component on iOS simulator with local and remote MP4s
- Root cause of infinite spinner: test URL returned 403, expo-av silently swallows HTTP errors
- Added 15-second load timeout to VideoPlayer so it shows error instead of spinning forever
- Confirmed expo-av works fine for both local files and remote URLs (when accessible)

## Next Step
1. Test tap-to-copy on keyframe images
2. Parallelize transition video generation — all I2V calls are independent (image pair i→i+1 has no dependency on pair j→j+1). Fire them concurrently with `asyncio.gather` or `ThreadPoolExecutor` instead of the current sequential loop in `video_service.py:562-664`. Expected to cut video phase from ~N×polling_time to ~1×polling_time.
3. Remove leftover Capacitor files
4. Delete `mobile/assets/Test_Video.mp4` (test artifact)
5. Implement design system from `design/DESIGN_SYSTEM_PRD.md`

## Open Questions
- Auth cookie extraction: will expo-web-browser's ASWebAuthenticationSession share cookies with fetch? (carried from session 13)
- Bleed audit marks bled elements as "renovated" causing early exit (fix deferred — feature-level)
- Should GPT be constrained from inventing structural elements on outdoor spaces? (carried from session 7)
- expo-av deprecated in SDK 54, removed in SDK 55 — plan migration to expo-video
