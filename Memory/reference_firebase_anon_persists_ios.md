---
name: Firebase anon persists on iOS
description: @react-native-firebase/auth DOES persist anonymous UIDs across kill+relaunch on real iOS device; if new anon UIDs appear on Firebase, trace them to a user action before suspecting a persistence bug.
type: reference
---

`@react-native-firebase/auth` Keychain persistence works for anonymous users on real iOS device (build 7, Session 39). Kill + relaunch preserves the anon UID AND the server-side usage state across multiple kill cycles. The free-tier gate (originally `UNAUTH_GEN_LIMIT=1` per-UID at Session 39; replaced Session 44 by the credit-balance gate at 10 starter credits per anon UID) survives as expected.

A new anon UID appearing on the Firebase Authentication console almost always traces to a specific user action — Sign Out in-app, or (on a fresh install) the first user action that triggers the lazy `signInAnonymously()` call. It is NOT a persistence failure.

Session 38 hypothesized a simulator quirk after kill+relaunch produced a new UID. Session 39 disproved it on real device: the "new UID" was from a Sign Out event that happened just before the kill. Clean isolated test (note UID → kill → relaunch → verify UID unchanged, hit Firebase console refresh) proves persistence works.

**How to apply:** When debugging anon Firebase sessions, always isolate the kill+relaunch from other auth actions. Trace each new UID on the console to a known user action before concluding persistence is broken. Don't rely on stale console views — hit refresh before verifying.
