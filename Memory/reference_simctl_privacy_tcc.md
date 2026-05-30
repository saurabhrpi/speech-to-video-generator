---
name: reference_simctl_privacy_tcc
description: Force TCC permission states (photos/camera/etc.) on the iOS simulator for testing without erasing
metadata:
  type: reference
---

Force a specific privacy/permission (TCC) state for an app on the booted simulator — no erase needed:

```
xcrun simctl privacy booted revoke photos com.saurabh.speechtovideo   # → denied
xcrun simctl privacy booted reset  photos com.saurabh.speechtovideo   # → undetermined (OS default / fresh-install)
xcrun simctl privacy booted grant  photos com.saurabh.speechtovideo   # → granted
```

Actions: `grant` | `revoke` | `reset`. Common services: `photos`, `photos-add`, `camera`, `microphone`, `location`, `contacts`, `media-library`, `all`. (`reset` returns to the OS default = undetermined.)

**Relaunch the app after changing state** so it reads the new TCC value cleanly: `xcrun simctl terminate booted <bid>` then `xcrun simctl launch booted <bid>` (terminate may say "found nothing to terminate" if it was already backgrounded — harmless; the launch is what matters). A cold launch of the expo dev client auto-reconnects to the running Metro URL.

This is how AIV-96 was verified across denied/undetermined/granted in one session without erasing the sim (erase = `xcrun simctl erase booted`, the heavier true-fresh-install reset). Pairs with [[reference_image_picker_no_permission_needed]]. App bundle id: `com.saurabh.speechtovideo`; primary sim UDID in [[reference_simulator_udid]].
