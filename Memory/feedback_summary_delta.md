---
name: Summary delta tracking
description: When /summary is called multiple times in a session, each summary should only cover changes since the last summary, not since the last git commit
type: feedback
---

When /summary is called multiple times in a conversation, each summary must only include the delta since the PREVIOUS summary — not since the last git commit. Track what was already summarized and exclude it from subsequent summaries.

**Why:** User received a duplicate summary that re-listed changes already covered earlier in the session. This wastes time and shows lack of awareness of conversation history.

**How to apply:** Before generating a summary, check if a prior summary was already given in the conversation. If so, only include changes made AFTER that point.
