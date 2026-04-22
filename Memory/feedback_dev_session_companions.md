---
name: Dev session companions + monitor noise filter
description: When firing up the dev sim/Metro, also start the log-stream/simctl-spawn/Nativewind watcher; and always strip simulator haptic-error noise from grep monitors
type: feedback
---

Two things to bake into every dev-session startup:

**1. Companion processes when starting the dev environment.**
When firing up the simulator and/or Expo Metro dev server, also start: a device log stream, `simctl spawn` for the bundle id, and the Nativewind/Tailwind watcher. Without these, app-side `console.log` output and live style changes don't surface during testing.

**Why:** Otherwise we waste time wondering why logs are silent or why styles aren't updating, and we miss real signal during integration tests.

**How to apply:** Whenever you (or the user) run `npx expo run:ios` for an interactive testing session, plan to also fire those companions. For quick rebuilds you can skip them, but anything involving the user driving the UI needs them.

**2. Monitor regex must strip simulator haptic noise.**
The iOS Simulator has no haptic engine, so any TextInput keystroke floods the system log with `CHHapticPattern` / `UIKBFeedbackGenerator` / `patternForKey:error:` lines. A loose monitor filter (e.g. matching `Error `) catches all of these and floods the chat with hundreds of lines per minute, drowning the real signal.

**Why:** This actually happened mid-session — had to stop and restart the monitor with a tighter filter while the user was typing.

**How to apply:** Always prefix monitor commands tailing the iOS Simulator log with:
```
grep -Ev --line-buffered "patternForKey|CHHapticPattern|UIKBFeedbackGenerator|NSPOSIXErrorDomain|NSCocoaErrorDomain|NSUnderlyingError"
```
before the positive-match grep. Keep the positive filter tight too (specific endpoint paths, RC events, NOBRIDGE markers — not bare words like `Error`).
