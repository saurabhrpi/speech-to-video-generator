---
name: NOW.md leanness rule
description: Trim NOW.md's REDUNDANCY — cross-section duplication, git/commit status, one-command-recoverable detail. Leanness is NOT minimizing item count and NEVER cuts unresolved/open work. When unsure whether to keep an open item, KEEP it.
type: feedback
---

NOW.md should be free of *redundancy*, not stripped to the bone. Leanness targets three buckets of **recoverable / repeated** content — it is NOT a mandate to minimize the number of open items, and it must never shrink the unresolved-work ledger.

1. **No cross-section duplication.** A fact appears in exactly one section. If "What happened" already states it, don't restate it verbatim in "Status" / "Next step" / "Open questions". (Forward-looking framing of a topic in "Next step" is not duplication — that's a distinct job.)

2. **No git/commit status.** No commit SHAs, commit messages, "N ahead of origin", or "uncommitted: X, Y, Z" inventories. `git status` / `git log` answers all of that in one command. (Same as rule 3 of [[NOW.md carryover rule]].)

3. **No one-command-recoverable detail.** If the next session can recover a *value* by running a single command (file contents, env values, deploy state, test output, version numbers), point to the command instead of embedding it. This bucket is about recoverable *values* ONLY — it does NOT apply to open questions, action items, or any unresolved work, even if those happen to reference a file or command.

**Leanness does NOT override [[NOW.md carryover rule]].** Unresolved items, action items, and open questions stay — verbatim, or migrated to a tracked artifact with a one-line pointer. "Tracked in AIV" is NOT a license to silently drop: keep it if it's load-bearing for the next session or the user values it. **When in doubt whether something is resolved enough to cut → KEEP it.** Over-trimming the open-questions ledger is the failure mode, not verbosity.

**Why:** NOW.md is a state-of-the-world handoff. Duplication and recoverable values make it longer without adding signal; dropping open work loses signal. The first is the only thing leanness removes.

**Incidents:**
- S76: created this rule, then immediately over-applied it at /close — dropped 3 still-open items from Open Questions (Beat It runtime-audio propagation, Bad-moonwalk AIV-103, Kling 600s max_wait) citing "lean" + "tracked = omit". User pushed back ("why did you remove so many unresolved action items?"); restored them. Lesson: the bias is toward KEEPING open items; leanness only ever removes redundancy/recoverable detail.
