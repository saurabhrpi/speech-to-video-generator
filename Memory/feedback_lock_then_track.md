---
name: Lock-then-track planning pattern
description: When facing non-blocker planning questions, lock with a reasonable assumption + note it as an assumption, don't ask. Resolve formally only when it becomes an actual blocker.
type: feedback
---

When facing planning questions (decisions, design choices, configs) that aren't immediate blockers, do NOT pause to ask the user. Lock with a reasonable assumption, note it as an assumption in the tracker (Linear SPE description, code comment, doc), and move on.

**Why:** Speed > clarity in early product-build phase. Clarity emerges as problems get solved. The user said it verbatim S60 (2026-05-09): "we can't be blocked on such things while the whole city is waiting to be built. We have to prioritize speed over clarity. Clarity will automatically come as we keep solving the problems." Asking for resolution on every minor question creates friction that compounds.

**How to apply:**
- When a tracker (SPE/issue) has multiple options, pick one with brief reasoning
- Add a "## OPTIONS LOCKED — S<N>" or "## ASSUMPTION LOCKED — S<N>" section noting the chosen path + reasoning + escape hatch (override anytime)
- **DO NOT mark the tracker Done** when locking an option or making an assumption. Keep it open. (User-clarified S60 — earlier "mark Done if planning question resolved" was wrong.)
- Add an explicit Status line: "Only option-locking confirmation is pending" OR "Only assumption confirmation is pending" — describe the trigger to close (e.g. "validates post-launch from conversion data" or "all child SPEs ship to published_status: published")
- Mark Done ONLY at the very end when (a) the underlying implementation work is fully done AND (b) the assumption has been validated (or is no longer worth tracking)
- Continue with downstream work in the meantime
- The user's anchor wording: "Just call it out, track it, note down the assumption made for the present and move on. We will do [the closing] towards the end."

**Exception — clarify before locking:** When the user's directive is based on a factual misunderstanding that has real downstream cost (legal, security, IP, data integrity), briefly clarify first. The user invited this in S60 with "if we can skip Vertex as well, then let's do that" — the "if" implicitly asked whether it was safe. Verifying revealed Vertex isn't a wrapper (it's direct Google with IP indemnity), so the user reversed and said "stay with Vertex."

**Anti-pattern:** Asking "should we use X or Y?" for every config value. The user explicitly does NOT want that during the build-out phase.
