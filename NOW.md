# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 54 — 2026-04-30 / 2026-05-02 — main + hotfix-build14 (closing)
**Status:** Build #14 resubmitted to Apple after a second rejection on Build #13. Resubmission cited 5.1.1(i)/5.1.2(i) (third-party AI data disclosure) and 2.1(b) (IAP "authorization attempt failed" on iPad). Both targeted fixes shipped on a hotfix branch from Build #13's exact commit, plus a backend privacy-policy text update deployed to Replit. Apple's third review is now pending.

## What happened this session

- **ToDo #1 — server-side concurrent-submit credit gate (Yellow): SHIPPED on main.** New `try_create_credit_job` in `utils/job_manager.py` does an atomic in-memory check + create under `_lock`: rejects if uid already has an unsettled credit-bearing job. `/api/generate/speech-to-video` swapped to use it; returns 429 `concurrent_job_in_flight` on collision. Mobile `blockedByInFlight` tightened to "any in-flight job blocks" + a friendly 429 alert in `gallery-store` for the multi-device collision case. Verified by 6 unit tests covering the exact TOCTOU window. Closes the adversarial-curl revenue leak. (Commit `3a0b704`.)
- **Gallery thumbnails (V2 polish, ex-NOW phantom #10): SHIPPED on main.** `expo-video-thumbnails` added; `lib/thumbnails.ts` extracts a 2-second frame on completion; `thumbnailUri` persisted on `GalleryJob`. Cards became pure-thumbnail (full-bleed image, no play-icon overlay, no save badge) — IG/TikTok pattern. `<Image onError>` clears stale URIs after rebuild-induced container UUID changes. (Commits `d449bcb` → `652f9b4`.)
- **Auto-play VideoPlayer + dedicated playback screen: SHIPPED on main.** Tap a thumbnail → push `clip/[id]` route. New screen has S2V title with chevron-only back, video letterboxed in upper half (`flex: 2`), prompt card with Copy button (`flex: 1`), three white circular action buttons (Create New / Save / Share) at the bottom (`flex: 1`). VideoPlayer auto-plays via `onLoad` — single-tap-to-play, no overlay. Save/Share use `expo-sharing` + `expo-file-system`. (Commits `01cbd9d` → `e876a65`.)
- **Apple App Review verdict on Build #13: REJECTED on 2.1(b) and 5.1.1(i)/5.1.2(i).** Apple tested on iPad Air 11-inch (M3) — `supportsTablet: false` doesn't actually prevent iPad review, only removes the Universal badge + iPad-screenshot requirement. The 2.1(b) error: "The authorization attempt failed for an unknown reason" — the same `ASAuthorizationError` first observed in S52 on a freshly-erased sim. Reviewer hits it every submission because their sandbox iCloud sign-in is always fresh and the auth daemon is always cold on first call.
- **Hotfix branch strategy from rejected commit's SHA.** Looked up Build #13's commit via `eas build:list` (`6971edaf...`), branched `hotfix-build14` from it, applied ONLY the rejection-targeted fixes — kept the diff to ~5 files vs. 20+ files of S54 work safely held back on main.
- **5.1.1(i)/5.1.2(i) fix.** New `DataSharingConsentModal.tsx` lists OpenAI Whisper + MiniMax Hailuo and the data each receives, with Decline / I understand. Speech tab gates BOTH mic-tap and text-Generate paths through it (audio goes to OpenAI even before the user taps Generate). Versioned AsyncStorage key `data_sharing_consent_v1`. Privacy Policy at `/privacy` extended with explicit per-provider data flow, links to each provider's policy, and Apple's required "equal or better protection" phrasing. Backend deployed on Replit; verified live with `curl -s https://speech-2-video.ai/privacy`.
- **2.1(b) fix.** Reproduced on iPad Air 11" (M4) sim with full `xcrun simctl spawn log show` trace. First attempt: tried immediate retry — failed because the second `signInAsync` was queued WHILE the user was still in Settings signing into iCloud. Correct fix: `requestAppleCredential` in `lib/auth.ts` catches the first failure, awaits `waitForAppActive(5min timeout)` until the user returns from Settings, waits 1s for the auth daemon to settle, then retries. Verified end-to-end on iPad sim → cold iCloud → Settings sign-in → return → name dialog → sandbox account → RC purchase. No red error.
- **Build #14 collision footgun discovered.** First EAS build from hotfix-build14 produced a duplicate Build #13: `eas.json` is `appVersionSource: "local"` + `autoIncrement: true`, hotfix branch had stale `app.json buildNumber: 12`, EAS bumped 12 → 13 (collision with the rejected Build #13 in ASC). Wasted one EAS credit. Recovery: app.json was now at 13 from the wasted build's local write, so re-running `eas build` bumped 13 → 14 cleanly. Memorialized.
- **Build #14 submitted + reply attached.** "Add for Review" clicked. Resolution-center thread has the privacy + IAP explanation. App Review Information notes include "designed for iPhone, please test on iPhone if possible" — soft hint, reviewer may or may not honor. Now in "Waiting for Review."
- **8 new memories captured.** RN v7 `headerBackButtonDisplayMode`, supportsTablet false doesn't block iPad review, Apple Sign In retry strategy (rewritten with the corrected fix), pattern-match the scenario not the prior fix (process feedback), FastAPI HEAD returns 404, Replit republish + curl race window, find git commit behind an EAS build, EAS local autoIncrement collides on hotfix branches.

## Next step — Session 55 (on resume)

**Wait for Apple's verdict on Build #14.** Three branches:

1. **Approved** → release v1.0 from ASC. Then **merge `hotfix-build14` → `main`**. Conflict risk in `mobile/app/(tabs)/index.tsx` (main has the S54 mobile-tighten for ToDo #1; hotfix has the consent-modal wiring) — both are additive in different parts of the file, should auto-merge but verify. After merge, **deploy backend from main to Replit** so the credit gate goes live. Pop any pending stash work (none currently — verified `git stash list` empty). Continue to v1.0.1 features (full prompt on dedicated playback screen — already shipped on main; ToDo #19 CustomerInfo listener; ToDo #27 verification logging).
2. **Rejected on something new** → fix on `hotfix-build14`, bump buildNumber once (avoid the local-autoincrement collision per `reference_eas_local_autoincrement_collision.md`), build, submit.
3. **Long delay (>72h)** → check ASC for reviewer messages.

**Uncommitted on hotfix-build14 right now (intentional, not lost):**
- `Memory/MEMORY.md` — index updates from S54
- `Memory/reference_eas_build_commit_lookup.md`, `Memory/reference_eas_local_autoincrement_collision.md` — newest two memory files
- `mobile/app.json` — buildNumber bumped to 14 by EAS during the actual Build #14 (don't manually change; will get committed organically)

## Open questions (carryover + new)

- **(S54 result, pending) Apple's third-attempt verdict.** Awaiting. If approved, the App Transfer plan to dad becomes possible.
- **(S54 new) When `hotfix-build14` merges back into main**, verify `mobile/app/(tabs)/index.tsx` merges cleanly (both branches edited it, in different blocks).
- **(S53 carryover) Dad's Apple Developer enrollment** still blocked on "Your account cannot be created at this time" — diagnosed as corporate-WiFi fingerprint trip. Retry from home WiFi via iPhone-native flow when dad has time.
- **(S53 carryover) M365/Entra tenant decision (ToDo #26)** — keep paying ~$6/mo for `support@speech-2-video.ai` or migrate to a free forwarder. Not urgent.
- **(S52 carryover from #6)** TestFlight smoke test on a physical device never happened. iOS sim + EAS build is the bet. If Apple ever rejects on a device-specific issue, this is the obvious next step.
- **(S48 follow-up B, still open) UX hole: home button shows action label only, balance only in Settings.** Decision needed post-launch.
- **(ToDo #19, S49+S48)** CustomerInfo listener for offline-replay + RC ingestion-lag. With user-facing Restore removed (S53), edge cases route to support email — pre-launch acceptable, must land before scale.
- **(ToDo #27, S54 new)** Pre-deploy `logger.info("concurrent_job_in_flight blocked uid=%s", ...)` line at the 429 raise site for prod visibility once Build #14 ships. Plus first-week prod log-grep for `"credits consume shortfall at completion"` (should never appear if the gate works).
- **Backend Apple precheck + clip-merge (Yellow #10).** Haven't verified `/api/auth/apple/precheck` + `/api/clips/merge` exist in `server.py`. Clip-orphan risk on anon→Apple collision.
- **(S43-era, future trigger)** RC `default` offering "Current" is implicit. Day a second offering is added, if `Purchases.getOfferings().current` returns null, check RC dashboard for explicit "Current" toggle.
