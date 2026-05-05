---
name: Same symptom, different cause — pattern-match the scenario, not the prior fix
description: When a memory says "X failed; Y worked", understand WHY Y worked. Two different scenarios can produce identical error messages but require different fixes. When a fix appears not to work in testing, check execution traces (logs/state) before assuming the code didn't load.
type: feedback
---

**Why:** S54, Apple Sign In retry. Memory `reference_apple_signin_first_attempt_fresh_sim.md` said "first ASAuthorization call fails, second works." I shipped immediate retry. User tested, retry "didn't work" — kept getting the same red error. I asked the user to verify Metro had picked up the change, suggested forcing reloads, etc. — wasted ~30 minutes spinning on the wrong hypothesis.

When I finally pulled `xcrun simctl spawn log show`, the truth was visible in 10 seconds:

```
16:36:34.111 — 1st signInAsync ERRORS  (user was in Settings)
16:36:34.154 — Our retry fires 33ms later  (user STILL in Settings)
16:37:10.643 — 2nd call ALSO ERRORS  (36s later, user back, daemon stale)
```

The retry WAS firing. The fix was just wrong. I had pattern-matched the *prior fix* ("retry once") without pattern-matching the *prior scenario* ("daemon cold on warm iCloud" vs. now "iCloud not signed in at all"). Two scenarios, same error message, different fixes:

- S52 scenario: iCloud already signed in, auth daemon just cold → immediate retry works.
- S54 reviewer scenario: iCloud NOT signed in → user goes to Settings; immediate retry queues a 2nd call while app is backgrounded; 2nd call ALSO fails. Need `await waitForAppActive` + settle delay before retry.

**How to apply:**

1. **When pattern-matching a memory, read the WHY, not just the WHAT.** A memory's recommended fix is a recommendation FOR ITS ORIGINAL CONTEXT. Verify your current scenario matches before applying the same fix. Especially when the user-visible symptom (an error string) is the same but the call-site state differs (foreground vs. background, signed-in vs. not, etc.).

2. **When a fix appears not to work in testing, check execution state before disputing the user.** Don't ask "are you sure the code reloaded?" first. Run `xcrun simctl spawn log show` (or equivalent: server logs, network traces, etc.). The logs almost always show what actually happened in 30 seconds. Until you have that evidence, the user's "it doesn't work" is more reliable than your "the code should work."

3. **Distinguish "fix didn't fire" from "fix fired but didn't help."** These need different next moves. If the fix didn't fire, debug the load path. If it fired but didn't help, the diagnosis was wrong — back to root-cause analysis. Logs are how you tell which.

4. **Two errors with the same string are not necessarily the same bug.** Especially generic errors like Apple's "authorization attempt failed for an unknown reason" or RC's "Purchase failed". Classify by call-site state, not error text.
