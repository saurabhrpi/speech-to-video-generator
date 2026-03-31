---
name: Never fill gaps with assumptions — only state what you've verified
description: CRITICAL — repeated violation. Never present assumed behavior as fact. If you haven't read and traced it end-to-end, you don't know it. This rule has been violated MULTIPLE times despite being in memory.
type: feedback
---

Never describe what something "typically contains", "usually does", or "should work" as if it's what's actually there. If you haven't read the file, traced the data flow, or verified the output, you don't know — say so, then check.

**Why:** Session 9 (2026-03-28): Made a backend code change and confidently told the user it would fix their problem — without tracing the frontend data flow. The fix was useless because `formPayload` is captured once at initial submit and never updated. Then doubled down by claiming the expensive model was being used when output.json clearly said `"video_model": "cheap"`. Two confident wrong answers in a row, both from assumptions, both with evidence RIGHT THERE in the codebase. This happened DESPITE this rule already existing in memory from a prior violation.

**Prior incident:** Session 6: Described contents of `.claude/` based on general knowledge, not inspection. Same pattern — presenting assumptions as facts.

**How to apply:**
1. Before ANY claim about runtime behavior: read the actual code path end-to-end, not just the part you're changing.
2. Before ANY claim about what value a variable holds: find the evidence (output file, log, code trace). No evidence = "I don't know, let me check."
3. Before ANY code fix: complete ALL 5 steps of Data Flow Verification. Not 3 of 5. All 5. The call site is where your last fix silently failed.
4. If you catch yourself saying "should", "would", or "will" about code behavior without having traced it — STOP. That's the assumption pattern. Replace with "let me verify."
5. Confidence without verification is the failure mode. Being slow and right beats being fast and wrong. EVERY TIME.
