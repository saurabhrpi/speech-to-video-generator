---
name: Change summary format — heading + short paragraphs
description: When asked to summarize changes since last commit, use a ~6 word heading followed by a body (max 800 chars) with each change as a separate paragraph.
type: feedback
---

When the user asks to summarize changes since the last git commit, format the output as:

1. A heading (~6 words)
2. A text body (max 800 characters total) with each change in its own paragraph

**Why:** User wants concise, structured summaries they can quickly scan — not bullet lists or verbose explanations.

**How to apply:** Any time the user asks for a summary of changes since last commit, use this exact format. Keep paragraphs tight and factual.
