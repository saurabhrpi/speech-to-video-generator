---
name: VideoPlayer debugging lessons
description: expo-av silently fails on HTTP errors; always verify URL accessibility before suspecting component
type: feedback
---

When debugging video playback issues in the app, check URL accessibility first (`curl -sI <url>`) before suspecting the expo-av component.

**Key learnings:**
- expo-av silently fails on HTTP errors (e.g. 403) — no `onError` callback fires, resulting in infinite spinner
- Test with local files first to isolate network vs component issues
- Google's sample video URLs (`commondatastorage.googleapis.com`) can return 403 — don't rely on them for testing
- expo-av is deprecated in SDK 54 and will be removed in SDK 55 — migration to `expo-video` will eventually be needed

**Why:** Spent significant time suspecting the component, considering migration to expo-video, and adding debug overlays — when the root cause was simply a 403 from the test URL.

**How to apply:** Always verify the URL works before debugging the player. Use `curl -sI` from the simulator or host machine. Test with a local file to confirm the component itself is functional.
