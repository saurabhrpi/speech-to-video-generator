---
name: kling-audio-test-policy
description: All Kling Motion Control dev/test runs use keep_original_sound="no". Audio only flips to "yes" at launch.
metadata:
  type: project
---

For every Kling Motion Control invocation during development, quality spikes, or A/B testing, set `keep_original_sound="no"` (Kling client default is `"yes"` — must be explicit).

**Why:** User policy set S66 during the V2 quality spike. Driving videos for V2 templates ship in two variants: `driving_video.mp4` (with audio) and `driving_video_silent.mp4` (audio stripped). For Bombale e2e in S65 the silent variant was uploaded to R2 and used in prod. The S66 policy extends that to all *test* iterations: audio off during iteration removes one variable, keeps spike outputs distraction-free for visual QA, and avoids prematurely committing to an audio decision per template.

**How to apply:**
- All spike scripts (`scripts/test_*`): pass `keep_original_sound="no"` to `KlingMotionClient.generate_and_poll(...)`.
- All dev/test invocations from the prod dispatcher (`_dispatch_motion_transfer`) during local development: same.
- The flip to `"yes"` happens **at launch time** as an explicit, deliberate change — not silently inherited from a default. When that flip happens, decide per-template whether each template ships with audio on or off.
