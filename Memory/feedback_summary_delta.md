---
name: Summary scope
description: /summary means summarize ALL uncommitted changes since last git commit — no delta logic, no session filtering
type: feedback
---

`/summary` = fetch `git diff HEAD` and summarize it. That's all. No delta tracking, no "since previous summary" logic, no filtering by which session the work happened in.

**Why:** User explicitly corrected overcomplicated delta logic. I had skipped the previous session's uncommitted server.py work from a /summary because I treated NOW.md's "What Happened This Session" block (and an earlier in-conversation summary) as prior checkpoints to clip against. The user wants it dead simple: uncommitted = summarize, regardless of when the work was done.

**How to apply:** When `/summary` is invoked, run `git diff HEAD` (or equivalent), summarize everything in it, done. Don't try to be clever about what the user "already saw." If they wanted a delta, they would ask for one.
