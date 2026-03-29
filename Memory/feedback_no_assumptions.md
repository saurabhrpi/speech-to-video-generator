---
name: Never fill gaps with assumptions — only state what you've verified
description: Never present assumed/typical behavior as fact. If you haven't read it, you don't know it. Always check first or say you don't know.
type: feedback
---

Never describe what something "typically contains" or "usually does" as if it's what's actually there. If you haven't read the file, directory, or output, you don't know what's in it — say so, then check.

**Why:** User caught me describing the contents of `.claude/` at project root based on general Claude Code knowledge, not actual inspection. I presented assumptions as facts. This violates the zero-hallucination standard in CLAUDE.md.

**How to apply:** Before stating what a file/directory/config contains, verify you've actually read it in this conversation. If you haven't, read it first or explicitly say "I haven't checked — let me look." Never bridge the gap with "it typically..." or "it can hold..." framed as a factual answer.
