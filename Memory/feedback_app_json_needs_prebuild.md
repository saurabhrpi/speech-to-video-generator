---
name: Run expo prebuild after app.json changes
description: app.json changes don't reach native Info.plist until expo prebuild is run; expo run:ios skips prebuild when ios/ exists
type: feedback
---

After any `app.json` change, run `npx expo prebuild` before the next `npx expo run:ios`. Without this, native config (Info.plist) stays stale.

**Why:** When `ios/` already exists, `expo run:ios` skips prebuild and builds from the existing native project. In Session 31, changed `userInterfaceStyle` to `"dark"` in app.json but Info.plist still said `Automatic`, so the app launched in light mode despite two full rebuilds.

**How to apply:** Only needed when `app.json` actually changes (rare — permissions, splash, bundle ID). Normal day-to-day startup is just `npx expo run:ios`.
