---
name: Sync Memory folders — every update goes to both locations
description: Memory exists in two locations. Every memory create/update/delete must be applied to both folders to keep them in sync.
type: feedback
---

Memory is stored in two locations:
1. `C:\Users\meets\.claude\projects\C--Users-meets-POCs-speech-to-video\memory\` (Claude Code auto-memory)
2. `C:\Users\meets\POCs\speech-to-video\Memory\` (project root copy)

Every memory operation (create, update, delete) must be applied to BOTH folders.

**Why:** User wants a version-controlled copy of memory in the project root alongside the Claude Code system copy. Having two copies means drift is a real risk.

**How to apply:** Whenever writing or editing any memory file (including MEMORY.md index), write the same content to both paths. Treat it as a single atomic operation — never update one without the other.
