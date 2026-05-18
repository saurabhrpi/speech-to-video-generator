---
name: NOW.md carryover rule
description: Don't drop unresolved content from NOW.md at /close. Trim only via resolution or migration. Top ~10 Open Questions cap, prefer items not tracked in Linear/AIV. Never include commit history.
type: feedback
---

When running the /close protocol on NOW.md, apply these three rules:

## 1. Don't drop unresolved content silently

Do NOT trim unresolved content from NOW.md in pursuit of brevity. This applies to **any** unresolved block: Open Questions / Flags, Verification plans that haven't run yet, Follow-ups from code review, Next-Step checklists, or any checklist-shaped item that represents concrete work.

An entry stays verbatim until one of these is true:

1. It was actually resolved this session (say so explicitly: "Resolved — [how]").
2. It was absorbed into a tracked artifact — Linear / AIV ticket, ToDo.md, LAUNCH_CHECKLIST.md, files under `QA/`, etc. AIV-prefixed items are by definition tracked in Linear and can be omitted from NOW.md without re-stating their existence (S66 user clarification).
3. The user explicitly tells you to drop or collapse it.

## 2. Open Questions: top ~10 cap, prefer untracked items

The Open Questions section ledger should be the **top ~10 open items**. Prefer items that are NOT already tracked in Linear/AIV — those have a home and the AIV/Linear ticket is the source of truth, so duplicating them in NOW.md is just two-place-bookkeeping.

Items tracked in AIV may still appear in NOW.md's top 10 if they are **load-bearing for the immediate next session** — e.g., a tracked ticket that blocks the literal "Next step" should still be flagged. But baseline assumption: tracked = omit.

Exceed 10 only when you have unresolved untracked items that wouldn't otherwise fit; never pad to 10 with low-priority tracked items.

## 3. Never include commit history in NOW.md

S66 user directive: NOW.md does not get a "Commits + push" block. Git is the commit log; NOW.md is for state-of-the-world recap, not history. The "What happened this session" prose can reference *what was shipped* (e.g., "deployed via Replit autodeploy") but should not enumerate commit SHAs or commit messages.

## Why (incidents)

- Session 44 close: dropped three Open Questions (Kling COGS placeholder, S42 paywall carryovers, CLAUDE.md S2V vision gap) chasing terse handoff. None were resolved. One (Kling COGS) had just been hardcoded verbatim into `CREDIT_COSTS` — exactly the kind of stale-assumption-in-code the flag exists to surface. User pushed back.
- Session 46 close: collapsed a 6-bullet verification script + 3-bullet follow-ups into a single paragraph. Both were actionable, unrun work. User pushed back. (The /close skill at `~/.claude/commands/close.md` had its "Keep it under 15 lines" line removed afterward — but the underlying carryover discipline stands regardless.)
- Session 66 close: I included a "Commits + push" block AND padded Open Questions with ~20 AIV-tracked items. User cut both, said "top 10, prefer untracked, no commits".

## How to apply

- Treat NOW.md as append-mostly at /close, EXCEPT for the Open Questions section which has a top-~10 cap and the no-commit-history rule.
- Summarize the "What happened" section tightly. Checklist-shaped / reference-shaped content that doesn't fit the top 10 → migrate to ToDo.md, AIV/Linear, QA/, LAUNCH_CHECKLIST.md, and leave a one-line pointer. Don't delete silently.
- Brevity is a goal for recap prose (Status + What happened). It does NOT apply to the unresolved-work ledger — but the ledger lives in tracked artifacts (Linear/AIV/ToDo.md), not in NOW.md beyond the top ~10 dashboard.
