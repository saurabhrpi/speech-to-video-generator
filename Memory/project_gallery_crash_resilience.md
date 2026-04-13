---
name: Gallery crash resilience
description: Lessons from Session 29-30 app crashes — persistence hygiene, TCC privacy crash, and how to find crash reports
type: project
---

## Crash #1: react-native-reanimated dev reload (Session 29)

Dev menu reload (Ctrl+Cmd+Z) crashed the app due to reanimated's known issue with native worklet teardown on JS reload. The crash wiped all Gallery tab metadata because:

1. `persist()` was fire-and-forget (`AsyncStorage.setItem` without await or error handling)
2. `hydrate()` had a silent `catch {}` that started fresh on any error — no logging, no fallback
3. No backup mechanism existed — once primary storage was lost, data was gone forever

**Fix applied (Session 30):**
- `persist()` now rotates: copies current primary → backup before writing new data, using `AsyncStorage.multiSet` (single SQLite transaction — atomic)
- `hydrate()` tries primary → falls back to backup → validates with `Array.isArray` → logs all errors
- On successful hydrate, saves backup for next time

## Crash #2: Missing NSPhotoLibraryUsageDescription (Session 30)

App crashed with SIGABRT on tapping the save/download button on Gallery thumbnail cards. Root cause: iOS TCC (privacy enforcement) killed the app because `NSPhotoLibraryUsageDescription` was missing from the built Info.plist. The `expo-media-library` plugin config was in `app.json` but hadn't been baked into the native project via `npx expo prebuild`. This likely worked before because the simulator had a cached permission grant from an earlier build, which was reset when the app crashed/reloaded.

**Fix:** Added `NSPhotoLibraryUsageDescription` to `app.json` → `expo.ios.infoPlist`, ran `npx expo prebuild --platform ios`, then `npx expo run:ios` to rebuild native binary.

## Key technical facts
- AsyncStorage uses SQLite — writes are atomic, so "corruption" is unlikely; the real risk is writes never completing before process death
- Unhandled promise rejections do NOT crash React Native apps (just yellow warning)
- react-native-reanimated dev reload crash is dev-only, does not affect production builds
- Videos saved to Camera Roll (via expo-media-library) are independent of Gallery tab state
- TCC privacy crashes show `namespace: TCC` in the termination details and tell you exactly which Info.plist key is missing
- Expo plugin configs in app.json only take effect after `npx expo prebuild` + native rebuild

**How to apply:** Any Zustand store with AsyncStorage persistence must have: (1) backup rotation in the write path, (2) fallback in the read path, (3) no silent catches, (4) input validation on deserialized data. For native crashes, always check `~/Library/Logs/DiagnosticReports/` before theorizing.
