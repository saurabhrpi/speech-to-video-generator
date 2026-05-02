---
name: Apple Sign In 1st attempt fails on fresh iCloud
description: After a fresh iCloud sign-in (sim OR real device with sandbox account), the first ASAuthorization call fails with "The authorization attempt failed for an unknown reason"; second succeeds. NOT a sim-only quirk — Apple reviewers hit this every submission. Auto-retry now implemented in mobile/lib/auth.ts requestAppleCredential.
type: reference
---

After ANY device or simulator has just signed into iCloud (Settings → Sign in to your iPhone, or a sandbox account login), the **first** ASAuthorization call from the app typically fails with:

> "The authorization attempt failed for an unknown reason"

The system auth daemon needs a moment to warm up after fresh iCloud sign-in. The second call always works.

**This is NOT a sim-only quirk.** Three confirmed instances:
1. S52 — iPhone 17 Pro Max sim after `simctl erase booted` + fresh iCloud sign-in.
2. S54 — iPad Air 11-inch (M4) sim, fresh iCloud sign-in via Settings during IAP test.
3. **Every Apple App Review submission** — reviewers use sandbox accounts on test devices freshly signed in. Build #13 was rejected on 2.1(b) specifically because of this red error. Apple's reviewer never knows "tap again" — they see the red error and cite the rejection.

**Mitigation in code (S54):** `mobile/lib/auth.ts` `requestAppleCredential` auto-retries once on any non-`ERR_REQUEST_CANCELED` error. **Critical detail discovered during S54 testing:** an immediate retry DOES NOT WORK when the user wasn't signed into iCloud at all (the most common reviewer case). iOS sends them to Settings to sign in; the immediate retry fires while the app is still backgrounded and ALSO fails with error 1000. The working strategy is:
1. `await waitForAppActive(5 min timeout)` — uses an `AppState` listener to wait for the app to be foregrounded again. Resolves immediately if already active (cold-daemon-on-warm-iCloud case).
2. `await sleep(1000)` — daemon settle delay; iOS needs ~1s after iCloud sign-in completes before it accepts a new ASAuthorization request.
3. Second `signInAsync` call.

Verified end-to-end on iPad Air 11-inch (M4) sim 2026-05-02: cold iCloud → tap Buy → Settings sign-in → return to app → name/email dialog → sandbox flow → RC purchase. No red error.

**Why we never hit this in our IAP testing earlier:** our test simulators had iCloud signed in days/weeks prior — daemon was always warm. Reviewer's environment is always fresh.

**Companion behavior to expect after retry succeeds:** iOS sandbox account selector appears (separate dialog, asks to "choose the only account listed" + password). This is iOS associating a sandbox tester with iCloud for IAP flows. Then the RC purchase sheet (App Store sandbox or RC Test Store, depending on `__DEV__`) appears.
