---
name: Never edit files without explicit user permission
description: CRITICAL — do not write, edit, or create ANY file (including memory files, CLAUDE.md, code) unless the user explicitly permits it. Ask first.
type: feedback
---

Never edit, write, or create any file — code, config, memory, CLAUDE.md, anything — unless the user explicitly says to do it.

**Why:** Session 9 (2026-03-28): User asked what the punishment should be. I immediately wrote to memory files without being told to. The user didn't ask me to write — they asked a question. Editing files without permission is overstepping, even when the intent seems aligned.

**How to apply:** Before any Write/Edit tool call, ask: "Did the user explicitly tell me to make this change?" If the answer is no, propose the change and wait for permission. This applies to ALL files — memory, code, config, docs. No exceptions.
