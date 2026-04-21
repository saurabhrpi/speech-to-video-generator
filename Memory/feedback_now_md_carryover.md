---
name: NOW.md carryover rule
description: Don't drop unresolved content (Open Questions, Verification plans, Follow-ups, action items) from NOW.md at session close — resolution or migration is the only exit criterion, not brevity
type: feedback
---

When running the /close protocol, do NOT trim unresolved content from NOW.md in pursuit of brevity. This applies to **any** unresolved block: Open Questions / Flags, Verification plans that haven't run yet, Follow-ups from code review, Next-Step checklists, or any checklist-shaped item that represents concrete work.

An entry stays verbatim until one of these is true:

1. It was actually resolved this session (say so explicitly: "Resolved — [how]").
2. It was absorbed into a tracked artifact (ToDo.md, LAUNCH_CHECKLIST.md, files under `QA/`, etc.) — mention the move.
3. The user explicitly tells you to drop or collapse it.

**Why (incidents):**
- Session 44 close I dropped three Open Questions (Kling COGS placeholder, Session 42 paywall carryovers, CLAUDE.md S2V vision gap) in pursuit of a terse handoff. None were resolved. One of them (Kling COGS) had just been hardcoded verbatim into `CREDIT_COSTS` in the same session — exactly the kind of stale-assumption-in-code the flag exists to surface. User pushed back.
- Session 46 close I collapsed the detailed 6-bullet "Verification after refactor" script and the 3-bullet "Follow-ups from code review" into a single Next-Step paragraph, again chasing brevity. Both were actionable, unrun work. User pushed back. (The /close skill at `~/.claude/commands/close.md` was subsequently edited to remove the "Keep it under 15 lines" line so future closes aren't nudged toward over-compression — but the underlying carryover discipline still stands regardless of what the prompt says.)

**How to apply:**
- Treat NOW.md as append-mostly at /close. Summarize the "What happened" section tightly, but checklist-shaped / reference-shaped content is carryover — keep it verbatim.
- If unresolved content is bloating NOW.md, migrate it (create/append to a file under `QA/`, `ToDo.md`, or `LAUNCH_CHECKLIST.md`) and leave a one-line pointer. Don't delete silently.
- Brevity is a goal for recap prose (Status + What happened). It does NOT apply to the unresolved-work ledger. Better to run long than to lose state.
