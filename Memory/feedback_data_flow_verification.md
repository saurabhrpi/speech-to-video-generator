---
name: ALWAYS complete all 5 steps of Data Flow Verification Protocol
description: After adding a new field/parameter, trace it end-to-end from origin to final usage. Never stop at the function return — verify the call site consumes it.
type: feedback
---

When adding a new data field (like MOTION_PROMPT), completing only steps 1-3 of the Data Flow Verification Protocol (origin → function signature → return dict) and skipping steps 4-5 (call site → end-to-end confirmation) caused a silent bug: GPT produced the field, the parser captured it, the function returned it, but the caller in video_service.py never stored it in the stage dict. Every transition video fell back to a generic prompt.

**Why:** This exact failure mode is what the protocol in CLAUDE.md was designed to prevent. The bug went undetected through a full generation run because the fallback silently covered the missing data. The user had to diagnose it by noticing the generic prompts in the output JSON.

**How to apply:** After implementing any new data field that flows across functions:
1. Start at the origin (GPT prompt / API response)
2. Verify the parser captures it
3. Verify the function returns it
4. **Read the call site** — does the caller extract and store it?
5. **Read the consumer** — does the downstream code access it from where it was stored?
Do NOT consider the implementation complete until you've read the actual code at every link in the chain. No assumptions, no skipping.
