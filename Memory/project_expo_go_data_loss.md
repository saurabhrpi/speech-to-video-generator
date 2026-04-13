---
name: Expo Go container resets wipe AsyncStorage
description: Gallery data was lost in Session 31 because Expo Go's scoped storage was wiped by a container reset
type: project
---

In Session 31 (2026-04-13), all Gallery data was lost. Root cause: the app had always been running through Expo Go, which stores AsyncStorage in a scoped path (`ExponentExperienceData/@anonymous/interior-timelapse-.../RCTAsyncLocalStorage/`). Between sessions, the Expo Go container was reset (likely Expo Go update to 54.0.6 or simulator recreation for iOS 26.4), wiping all scoped project data.

**Why this matters:** AsyncStorage is the only persistence layer for Gallery jobs. No server-side backup exists. A container reset means total data loss.

**How to apply:** Always use dev client builds (`npx expo run:ios`) so the app gets its own container. Consider server-side backup for Gallery data as a future resilience layer.
