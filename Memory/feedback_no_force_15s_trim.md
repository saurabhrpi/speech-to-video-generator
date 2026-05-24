---
name: no-force-15s-trim
description: Don't hard-trim driving videos to 15s. Allow natural length up to Kling's video-orientation cap (30s). 15s was a runbook convenience, not a Kling limit.
metadata:
  type: feedback
---

When trimming a source MP4 for a V2 template's driving video, do NOT use `-t 15` as a hard cap. If the natural clip is a couple seconds over (e.g. 16-18s), keep the full natural length. Kling's `character_orientation="video"` mode caps at 30s, not 15s — the 15s figure in the runbook was a default-for-cost convenience, not a hard limit.

**Why:** Forcing 15s when the natural clip is 17s drops the last few seconds of the dance, often clipping the climax move. The user explicitly called this out S75 — they're fine with a couple seconds over 15s.

**How to apply:** When following the V2 template runbook step 2 (trim source MP4):
- Inspect source duration with ffprobe
- If natural length (after start-offset trim) is ≤30s: use full natural length, omit `-t` or set it generous (e.g. `-t 25`)
- If natural length >30s: trim to 30s (Kling's hard cap on video orientation)
- Only use `-t 15` when the source is genuinely long and the dance loops fine at 15s

See also: [[no-overfit-prompts]] (similar "don't default unnecessarily" principle).
