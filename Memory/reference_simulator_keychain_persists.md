---
name: Simulator Keychain survives uninstall
description: xcrun simctl uninstall does NOT wipe iOS Simulator Keychain. Firebase anon UIDs persist across app reinstall. Use xcrun simctl erase booted for a true fresh-install test.
type: reference
---

iOS Simulator Keychain is not tied to the app sandbox. Running `xcrun simctl uninstall booted <bundle_id>` removes the app binary and its Documents/Caches, but Keychain entries stick around. Firebase's RN SDK (`@react-native-firebase/auth`) stores its refresh token in Keychain, so on reinstall the SDK finds the old token → server honors it → same UID returns. No new anon user is created.

**How we got burned (Session 41):** Investigating a suspected "lazy anon sign-in on fresh install" bug, we uninstalled via `simctl uninstall` and relaunched. Firebase console showed no new UID, which seemed to confirm the bug. Actually the listener was firing correctly with a *persisted* anon user (`UjWTMXlTxNdwaFRw2GqMGtqgYS62`), RC `logIn` ran successfully with a valid Firebase UID, and the "lazy" path was never exercised because Firebase already had a user. The Metro log at `/tmp/metro.log` proved it — `getIdToken` warning fired (only possible with a non-null currentUser) and RC's `LogInOperation` completed with the persisted Firebase UID before any user interaction.

**How to apply:**
- To reproduce a TRUE first-install state on simulator, use `xcrun simctl erase booted` (wipes Keychain, photos, settings, all apps — requires simulator restart). Plain `uninstall` is insufficient.
- When "no new UID appeared" in a Firebase auth test, don't conclude the code path didn't run — check Metro logs first for the actual listener/RC behavior. The persisted UID can look like a no-op.
- `tee /tmp/metro.log` is Metro's stdout capture on this project — good diagnostic surface when you don't have direct terminal access.
