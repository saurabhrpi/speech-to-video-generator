---
name: Don't trust Explore agents on load-bearing claims
description: Explore subagents can confidently misreport what code does; verify anything that would change a recommendation before relying on it
type: feedback
---

Treat Explore agent output as a set of *candidates and leads*, not as ground truth. If a claim from an Explore agent would change your recommendation, architecture decision, or diff, independently verify it with a direct Grep or Read before acting.

**Why:** In session 32, an Explore agent confidently reported that the timelapse pipeline "already implements polling as a reference" via `mobile/lib/polling.ts::pollJob`. I quoted that to the user as justification for a "switch speech-to-video to the pattern timelapse already uses" recommendation. The user pushed back — turned out `pollJob` was dead code, unused anywhere in the app. Both timelapse and speech-to-video actually used `streamJob` (SSE). The agent saw `pollJob` was defined, saw callbacks with "same interface," and leapt to "it's wired up." A one-line Grep would have caught it. The user caught it before I embarrassed myself further.

Failure mode is predictable: agents pattern-match existence of code to existence of behavior. Dead code, feature-flagged code, and code behind unused branches all look identical to active code unless you check call sites.

**How to apply:**
- For any agent claim of the form "X uses Y" or "the code already does Z," run `Grep` for a caller/usage before citing it.
- For broad "what's here" surveys (file layout, where things live, what the surface area looks like), agent output is still useful — just don't trust the *verbs* (uses, does, calls, implements) without a check.
- When delegating investigation, ask the agent to quote file paths + line numbers of actual call sites, not just definitions. Missing call sites in the response = the agent didn't check.
- If a claim is load-bearing for a change you're about to make, verify it yourself. Delegating understanding is the trap.
