---
name: Always use expo run:ios, never expo start
description: expo start uses Expo Go which has fragile scoped storage; expo run:ios builds a dev client with its own app container
type: feedback
---

Always launch the mobile app with `npx expo run:ios`, NEVER `npx expo start --ios`.

**Why:** `expo start` runs through Expo Go, which stores AsyncStorage data inside Expo Go's scoped container (`ExponentExperienceData/@anonymous/...`). This data gets wiped when Expo Go updates or the simulator is reset. `expo run:ios` builds a standalone dev client under the app's own bundle ID (`com.saurabh.interiortimelapse`), giving it an independent sandbox that survives Expo Go changes.

**How to apply:** Any time the user asks to start the simulator/app, or you need to launch the app for testing, use `cd mobile && npx expo run:ios`. Never use `expo start` or `expo start --ios`.
