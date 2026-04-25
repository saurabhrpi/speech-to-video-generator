---
name: Simulator Keychain survives uninstall (and sometimes survives `simctl erase booted` too)
description: xcrun simctl uninstall does NOT wipe iOS Simulator Keychain. Firebase anon UIDs persist across app reinstall. `simctl erase booted` is UNRELIABLE for Keychain wipe (S52 burn) — use Simulator GUI Device → Erase All Content and Settings, or sidestep entirely by wiping the Firestore credit doc.
type: reference
---

iOS Simulator Keychain is not tied to the app sandbox. Running `xcrun simctl uninstall booted <bundle_id>` removes the app binary and its Documents/Caches, but Keychain entries stick around. Firebase's RN SDK (`@react-native-firebase/auth`) stores its refresh token in Keychain, so on reinstall the SDK finds the old token → server honors it → same UID returns. No new anon user is created.

**How we got burned (Session 41):** Investigating a suspected "lazy anon sign-in on fresh install" bug, we uninstalled via `simctl uninstall` and relaunched. Firebase console showed no new UID, which seemed to confirm the bug. Actually the listener was firing correctly with a *persisted* anon user (`UjWTMXlTxNdwaFRw2GqMGtqgYS62`), RC `logIn` ran successfully with a valid Firebase UID, and the "lazy" path was never exercised because Firebase already had a user. The Metro log at `/tmp/metro.log` proved it — `getIdToken` warning fired (only possible with a non-null currentUser) and RC's `LogInOperation` completed with the persisted Firebase UID before any user interaction.

**How we got burned again (Session 52):** This memory previously recommended `xcrun simctl erase booted` as the fix. **It didn't actually wipe Keychain.** After erase + `expo run:ios` the persisted anon UID returned, attached to its old Firestore credit doc with `balance: 0`, and the user saw 0 credits on what should have been a fresh install. Firebase Auth Console confirmed: NO new anon user was created — the most-recent anon UID was from yesterday's testing.

Plausible reasons `simctl erase booted` may silently no-op Keychain:
- Requires the device to be shut down first; running on a booted device may partially fail
- Modern Xcode versions may handle Keychain partition differently
- Some other quirk we haven't isolated

**How to apply:**
- To get a TRUE first-install state on simulator, use one of these (in order of reliability):
  1. **Simulator GUI: Device menu → Erase All Content and Settings** — bulletproof, the path Apple supports
  2. **CLI sequence**: `xcrun simctl shutdown booted && xcrun simctl erase <udid> && xcrun simctl boot <udid>` — shutdown first, then erase. UDID from `xcrun simctl list devices | grep Booted` first.
  3. **`xcrun simctl erase booted`** — DO NOT TRUST. Often silently leaves Keychain intact. If you must use it, verify by checking Firebase Auth Console for a new anon user immediately after relaunch.
- **Sidestep entirely for credit-balance / per-user-state testing**: delete the user's doc from Firestore (e.g., `credits/{uid}`) and force-quit + relaunch the app. The server's `ensure_anon_starter` will recreate it on next session call with the current starter amount. This proves the server path works without needing a fresh Keychain.
- When "no new UID appeared" in a Firebase auth test, don't conclude the code path didn't run — check Metro logs first for the actual listener/RC behavior. The persisted UID can look like a no-op.
- `tee /tmp/metro.log` is Metro's stdout capture on this project — good diagnostic surface when you don't have direct terminal access.
