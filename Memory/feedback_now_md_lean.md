---
name: NOW.md leanness rule
description: Keep NOW.md as lean as possible — no cross-section duplication, no git/commit status, no detail that's one-command-checkable or not immediately useful to the next session.
type: feedback
---

Keep NOW.md as lean as possible. At /close, before writing, strip anything in these three buckets:

1. **No cross-section duplication.** A fact appears in exactly one section. If "What happened" already states it, don't restate it in "Status", "Live state", "Next step", or "Open questions". Each section has a distinct job — recap vs. current state vs. forward work — and the same sentence shouldn't live in two of them.

2. **No git/commit status.** No commit SHAs, commit messages, "N ahead of origin", or "uncommitted: X, Y, Z" inventories. Git is the source of truth for all of that — `git status` / `git log` answers it in one command. (Same directive as rule 3 of [[NOW.md carryover rule]], stated here as a leanness principle too.)

3. **No one-command-checkable or non-immediately-useful detail.** If the next session can recover a detail by running a single command (file contents, env values, deploy state, test output, version numbers), don't embed it — point to the command or artifact instead. Drop "overly elaborate" detail that won't be immediately actionable next session.

**Why:** NOW.md is a state-of-the-world handoff, not a changelog or a data dump. Duplication and recoverable detail make it longer to read and let sections drift out of sync. User directive S76.

**How to apply:** Lean ≠ dropping unresolved work — [[NOW.md carryover rule]] still governs: unresolved items stay verbatim (or migrate to a tracked artifact with a pointer). Leanness applies to *recap prose, duplication, and recoverable detail*, never to the unresolved-work ledger. When in doubt: "can the next session get this from one command?" → yes = cut it; "is this said elsewhere in the file?" → yes = cut the duplicate.
