# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 32
**Date:** 2026-04-14
**Branch:** main
**Status:** SSE-kill bug fix **implemented** for speech-to-video (SSE → polling, `'paused'` state, AppState + NetInfo auto-resume). Code complete, type-checks clean. **NOT YET TESTED.**

## Bug Context (from Session 31 self-test)
During self-test I tried using the app while on a FaceTime call AND while backgrounding it. The UI showed "network connection was lost" — and no video appeared. Felt like ~$1 wasted. Server logs confirmed both jobs (`387451605938268`, `387453794079043`) completed cleanly on MiniMax — the SSE stream just died when iOS suspended the app, and nothing re-retrieved the result. That's the bug this session fixes.

## What Happened This Session
- Replaced `streamJob` with `pollJob` in the speech-to-video path only. Added `'paused'` to `GalleryJob.status`, NetInfo + AppState listeners that call `resumePausedJobs()`, and a cloud-offline icon in gallery. Files: `mobile/lib/api-client.ts` (added `HttpError`), `mobile/lib/polling.ts` (added `PollError` with `ERR_JOB_NOT_FOUND` / `ERR_CONNECTION_LOST`), `mobile/store/gallery-store.ts` (main surgery, extracted `runPoll()` helper), `mobile/app/_layout.tsx` (two new useEffects), `mobile/app/(tabs)/gallery.tsx` (paused card UI).
- Verified backend `GET /api/jobs/{id}` is pipeline-agnostic — no backend changes needed.
- Discovered `pollJob` was dead code before this session; BOTH pipelines used `streamJob`. Explore agent reported timelapse "already polls" — wrong. User caught it. Timelapse SSE-kill bug still exists; deferred.
- Tried `expo run:ios --device` for testing — blocked by the same Session-31 `errSecInternalComponent` keychain issue. Pivoted to simulator plan.
- Saved learning: `Memory/feedback_explore_agent_trust.md` — verify load-bearing Explore claims with direct Grep.

## Next Step
`cd mobile && npx expo run:ios` (simulator). Run Test 2 (offline → paused → resume), Test 3 (force-quit + relaunch), Test 5 (happy path). If all pass → EAS Build + TestFlight for Test 1 (FaceTime mid-job, the Session-31 repro) → invite friend.

## Open Questions
- **Observation:** red line at top of app briefly appeared when FaceTime ended. Is it the iOS-system audio-session transition indicator and not our app? Is it a concern only if the app actually grabs the mic on foreground?


## ToDo's
1. **Recovery attempt for the two lost videos (Session 31).** MiniMax `download_url` TTL is 1 hour — by now almost certainly expired. Task IDs: `387451605938268`, `387453794079043`. Worth checking if MiniMax client has a "fetch-by-task-id" helper that bypasses the TTL, otherwise close this out. Besides: a.) if we add SSE recovery, do we also need server-side cancel-on-client-disconnect? (Separate concern — cost control when user truly abandons).
b.) Push notification on completion as a v2 improvement (real fix for "user walks away for 20 min"). 
2. **Test the SSE-kill fix.** Refer to Test_plan.md for more details. (a) Simulator: `npx expo run:ios` → Test 2 (toggle Mac Wi-Fi off for ~50s mid-job → card flips to paused/cloud-offline → Wi-Fi on → auto-resume → completes), Test 3 (pause state + force-quit + relaunch → `hydrate()` resumes), Test 5 (happy path regression — progress updates every ~5s now, was sub-second under SSE). (b) Device: EAS Build → TestFlight → Test 1 (FaceTime mid-job).
3. **Invite friend as internal tester** via App Store Connect (Users and Access → Developer role → Interior Timelapse only; then TestFlight → Internal Testing group). Blocked by #2.
4. **Apply the same SSE → polling fix to the timelapse pipeline** (`mobile/store/pipeline-store.ts` — two `streamJob` call sites at lines 94 and 174). Same class of iOS-background bug; just hasn't surfaced because we haven't tested timelapse while backgrounded. After this, `mobile/lib/streaming.ts` can be deleted.
5. Confirm Session 29 dev-menu-reload crash root cause. Reproduce, retrieve `.ips` from `~/Library/Logs/DiagnosticReports`, verify reanimated frames in stack trace.
6. Re-test with Kling model (only Hailuo tested so far).
7. Test the recorded-audio path (only typed-prompt tested so far).
8. Simulator paste keeps breaking. `simpaste` alias is a workaround, not a fix. Find a permanent solution.
9. Fix Button.tsx type error (`mobile/components/Button.tsx:87`). Pre-existing, non-blocking — app runs fine — but `tsc --noEmit` is noisy and `<Button>` loses autocomplete. One-line fix: replace `require('react-native').Pressable` with a top-level `import { Pressable }` so `createAnimatedComponent` can infer prop types.
10. Local `expo run:ios --device` still blocked by Session-31 keychain issue (`errSecInternalComponent` when codesigning React.framework). EAS Build works fine; simulator works fine; only physical-device dev builds are broken. Low priority — EAS is the working path for device testing. See `Memory/reference_keychain_reset_recovery.md` for what was already tried.
