# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 38
**Date:** 2026-04-18
**Branch:** main
**Status:** Apple Sign In collision path fixed in code + verified on simulator. Fix NOT YET shipped — next session's first task is EAS rebuild + resubmit to TestFlight.

## What Happened This Session

- **Built + shipped build `1.0.1 (6)` to TestFlight** carrying Session 37's `e5c5f6d` auth-UI fix. Build took ~5 min, submission via `eas submit --platform ios --latest --non-interactive` went clean.
- **Installed on iPhone, hit a new bug immediately:** Sign In with Apple popped `[auth/unknown] Duplicate credential received. Please try again with a new credential.` Screenshot captured.
- **Root-caused the bug.** Apple identity-token + nonce pair is single-use. `lib/auth.ts::signInWithApple` did: `linkWithCredential(appleCred)` → failed with `auth/credential-already-in-use` (Apple ID was linked to yesterday's UID `z3S9exmD...`) → swallowed the error and called `signInWithCredential(appleCred)` with the **same** appleCred → Firebase rejected the reused nonce.
- **Verified with web research** (RN Firebase GitHub issues #272, #3952, RNFB Social Auth docs): Apple nonce single-use rule is real; the iOS-native `FIRAuthErrorUserInfoUpdatedCredentialKey` escape hatch is NOT surfaced by `@react-native-firebase/auth`'s JS layer (returns `null`). Only working fallback is to request a **fresh** Apple credential (new `signInAsync` call) and retry with that.
- **Fix applied to `mobile/lib/auth.ts`** (uncommitted): extracted `requestAppleCredential()` helper; the `credential-already-in-use` catch block now calls it a second time to get a fresh token/nonce, then `signInWithCredential(freshCred)`.
- **UX trade-off evaluated and accepted.** In the collision case (user's Apple ID already linked to another UID — rare, only triggers on reinstall or second device) the code invokes `signInAsync` twice back-to-back. User explicitly flagged this as "bad UX even if rare."
- **Agreed plan:** ship the double-sheet patch NOW for the short-lived standalone-banner path, then replace the whole flow with a proper single-sheet + backend-merge architecture as part of the RevenueCat paywall work (where sign-in rightfully lives per the monetization model).
- **Keychain persistence of Firebase auth confirmed (iOS).** User deleted + reinstalled the app on device; Firebase restored the same `z3S9exmD...` UID from iOS Keychain. Clean test requires in-app Sign Out *before* delete — that's what wipes Keychain. Added to the next-session playbook.
- **Simulator verification run (`npx expo run:ios`):**
  - First build failed with the `RNFBApp.* non-modular header` error — local `ios/` directory didn't have the `forceStaticLinking` from `app.json`. `expo run:ios` skips prebuild when `ios/` exists. Fix: `npx expo prebuild --platform ios --clean && npx expo run:ios`. Existing memories `feedback_app_json_needs_prebuild` + `reference_rnfb_modular_headers` already cover this case; didn't add a new memory.
  - Device checklist on simulator: **tests 2, 3, 4 passed cleanly.** Sign-in works; unlimited gens post-sign-in; sign out creates a new anon UID; kill+relaunch preserves signed-in session.
  - **Test 1 (clips preservation) re-diagnosed:** pre-sign-in clip remained visible post-sign-in, which contradicted my initial prediction. Investigation showed the mobile UI is reading from `mobile/store/gallery-store.ts` (local AsyncStorage key `gallery_jobs`) — **not** UID-scoped. `/api/clips` backend path IS UID-scoped (`server.py:185`). So local-device clip visibility is auth-agnostic by design/accident; cross-UID data loss is a server-side concern that lands with RevenueCat precheck+merge.
  - **Test 5 (kill+relaunch as anon):** new anon UID appeared instead of reusing the one from test 3. Likely a known `@react-native-firebase/auth` simulator quirk (Keychain persistence doesn't faithfully reproduce on simulator). Needs verification on real device after the EAS rebuild; not blocking.
- **Cosmetic observation:** on the successful simulator sign-in, Apple returned email but not full name. This is expected — Apple only returns full name on the *first* authorization of an app; subsequent sign-ins omit it regardless of requested scopes.
- **"Tap 1 did nothing" mystery on simulator** — first Sign-In-with-Apple tap after returning from Settings (where the user had to initially configure an Apple ID) completed the sheet but produced no state change, no error. The `settings.tsx:21` handler only silently swallows `ERR_REQUEST_CANCELED`. Not reproduced on the second tap (which worked). Not blocking; chase with Metro/Xcode logs only if it recurs.
- **New memories:**
  - `memory/feedback_eas_user_runs.md` — For EAS inspect/submit (`build:view`, `submit`), give the user the command — don't run it. Queueing with `--no-wait` is fine for me.
  - `memory/feedback_never_lose_clips.md` — Hard cross-cutting rule. No auth, migration, or account flow may orphan user clips (free or paid). Future auth flows must either link-in-place or do a cross-UID clip merge when the active UID changes.
- **LAUNCH_CHECKLIST.md updated.** RevenueCat item (#2) now carries an explicit line for Apple precheck (Firebase Admin SDK `get_user_by_provider_uid` to detect Apple-ID-already-linked collisions *before* attempting linkWithCredential, avoiding nonce consumption + second sheet) + a backend clip-merge endpoint for the collision branch. Removes the Session-38 double-sheet patch once RevenueCat work lands.

## Verdict on the Simulator Run (verbatim, to preserve context for next session)

> Fix is working for the correctness case it targets (`auth/credential-already-in-use` → fresh cred → signed in, banner clears). Test #2, #3, #4 all passed. #1 is a misread (local vs server clip storage), #5 is a simulator quirk worth re-running on device but not blocking.

## Next Step

**EAS rebuild + resubmit to TestFlight carrying the `mobile/lib/auth.ts` fix.** `e5c5f6d` is on the shipped build `1.0.1 (6)`; the new collision fix is uncommitted on disk. Flow (same as this session):

1. Commit `mobile/lib/auth.ts` (and this NOW.md + memory changes + ToDo.md if applicable).
2. `cd mobile && eas build --platform ios --profile production --non-interactive --no-wait` (I can run this — queueing is fine).
3. **User runs** `eas build:view <id>` periodically and `eas submit --platform ios --latest --non-interactive` when finished (per `feedback_eas_user_runs.md`).
4. Install new build from TestFlight.
5. Resume the device checklist: this time specifically watch for (a) single-sheet vs double-sheet on collision (should be double on device or silent-second on Apple cache); (b) anon UID persistence across kill+relaunch — if the simulator quirk doesn't reproduce on device, this passes; (c) whether the "tap 1 did nothing" mystery recurs (if yes, grab Metro + Xcode logs).

## Open Questions / Flags

- **"Sign in required" banner still a standalone gate.** Explicitly violates `project_monetization_model.md`. Stays in place until RevenueCat work lands; captured in `LAUNCH_CHECKLIST.md` #2.
- **Double-sheet Apple flow** — acceptable short-term, replaced by single-sheet precheck + clip merge in RevenueCat work.
- **Server-side clip preservation on UID change** — still unaddressed for the collision case (fresh anon's server-side clips get orphaned on fallback sign-in). Mobile local gallery-store hides this visually on the same device, but cross-device reinstall would surface the data loss. Part of the RevenueCat clip-merge endpoint spec now.
- **Simulator anon persistence quirk** — verify on real device.
- **`settings.tsx` "tap 1 did nothing" silent failure** — possibly an `ERR_REQUEST_CANCELED` that fires despite apparent sheet completion. If it recurs on device, instrument the catch to surface something instead of silent swallow.
- **SESSION_SECRET deletion from Replit** — carryover from Session 36, still unverified. Inert either way.
- **4.3a carryover risk** — still outstanding for Task 10.
- **Account deletion UI (Apple 5.1.1(v))** — still deferred.

## Session Artifacts

**Committed (3 commits ahead of `origin/main`, unchanged from Session 37):**
- `232ccc6` Commit GoogleService-Info.plist for EAS builds + bump to 1.0.1
- `da580de` Force-static-link RNFBApp/RNFBAuth to fix Xcode build
- `e5c5f6d` Apple Sign In: clear loginRequired after anon-link

**Next-session commit plan:** bundle the auth.ts fix + all memory/doc changes into a single commit ("Apple Sign In: fresh cred on linkWithCredential collision") before kicking off the EAS rebuild.

**Shipped, running on user's iPhone as `1.0.1 (6)`:** has the banner-clear fix but NOT the collision fix. Users hitting the `credential-already-in-use` code path will still see the `Duplicate credential received` alert until build 7 ships.
