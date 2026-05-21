---
name: moving-overlays-degrade-kling-quality
description: Bouncing TikTok logos / animated username captions baked into a driving video can manifest as dancer-glide and apparent camera jitter in Kling Motion Control output — even when the source camera is genuinely static. Prefer clean sources; static overlays are fine, moving ones are not.
metadata:
  type: reference
---

MOVING / ANIMATED overlay elements baked into a Kling Motion Control driving video — bouncing TikTok watermarks, animated username captions, jumping creator handles — can degrade output in subtle ways beyond the obvious "overlay smear" artifact. Observed symptoms:

- Dancer appears to float / glide on the ground, not anchored to the floor
- Apparent camera jitter / wobble in the output, even when the source camera is genuinely static
- General "AI-looking" unnatural motion that's hard to attribute to any single visible cause

**Why:** S71 Bad template. First Kling attempt used `Bad_clip.mp4` (576×1024 TikTok download with the TikTok logo bouncing + the @username caption animated). Output had dancer-glide + apparent camera motion that the user flagged as "very unnatural — quite obvious it's AI generated." After ruling out camera motion in the source (the dancer was just moonwalking across the floor — see [[video-motion-needs-human-eye]]), the moving watermarks were the most plausible remaining variable. Swapping to `Bad_720p.mp4` (different source, cleaner overlays) immediately produced an awesome output — same NBP edit, same pose, same scene description, only the driving video changed.

**How to apply:** When sourcing driving videos for Pipeline A (Kling Motion Control), prefer clips with NO watermark, or STATIC watermarks at most. BOUNCING / ANIMATED overlays are a reason to re-source the clip, not just to mask. Pairs with [[kling-driver-quality-checklist]] §3 — that memory's "the Beat It final used a static LCD playing the MV and Kling handled it cleanly" finding is consistent: static overlays are fine, moving ones are not. Static camera (#1 in that checklist) is still the load-bearing requirement; moving-overlay risk is incremental on top, but can be the difference between "great" and "uncanny" once camera-motion is ruled out.
