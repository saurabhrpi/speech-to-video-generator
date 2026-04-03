---
name: Analyze before concluding
description: Don't jump to lazy conclusions — analyze the evidence, think in multiple directions, and only make defensible arguments
type: feedback
---

When the user presents a problem (e.g. "stitching is slow"), DO NOT spit out the first thing that comes to mind (e.g. "Replit is slow, move platforms"). Instead:

1. **Analyze the evidence first.** Look at the logs, the architecture, the data. The answer is often right there.
2. **Think in multiple directions.** Ask "what else is happening on the server during this?" "What architectural patterns could address this?" Generate at least 2-3 hypotheses before presenting one.
3. **Make defensible arguments only.** Every suggestion must withstand 3 follow-up questions. If you can't defend it, don't say it.
4. **Don't fold immediately when challenged.** Either defend with evidence or acknowledge you didn't do the analysis — don't just agree to agree.
5. **Don't blame the platform/infra as a lazy default.** Architectural issues are architectural, not platform-specific.

**Why:** User called out a pattern of lazy analysis — jumping to surface-level conclusions, giving undefensible advice ("move off Replit"), folding under pushback, and failing to generate ideas (SSE was the right answer, evidence was in the logs, but I didn't think to look).

**How to apply:** Every time a problem is presented, pause. Read the evidence. Think of at least 2-3 possible causes/solutions before responding. The SINGLE most important skill is to think in different directions and explore ideas.
