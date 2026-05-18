---
name: kling-audio-test-policy
description: S67 launch-time flip — audio is controlled per-template via Firestore template.audio_enabled, default off. Spike scripts still default to silent.
metadata:
  type: project
---

S67 update: the S66 hardcoded `keep_original_sound="no"` in `_dispatch_motion_transfer` is gone. The motion-transfer dispatcher now reads `template.audio_enabled` (Firestore field) and passes `"yes"` when the flag is true, `"no"` otherwise. Default missing/False = silent, matches the original test-policy default so behavior is unchanged for templates that haven't been explicitly opted in.

**Why:** Per-template control was the planned exit from the S66 hardcoded policy. Each template can have a different audio decision based on whether the driving-video soundtrack is good (music dance trends → audio on) or distracting (background ambient → audio off).

**How to apply:**
- Spike scripts (`scripts/test_*_chain.py`): default to silent. Use `--keep-audio` flag when you specifically want to test audio output for a template (added on `test_gangsta_chain.py` S67).
- Prod dispatcher: reads `template.audio_enabled` per gen. No code edit needed to flip a template's audio — use `scripts/set_template_audio.py --template-id ... --enable/--disable`.
- For V2.0.0 launch: walk each Pipeline A template and decide individually. Default off remains a safe ship state — only flip on after verifying the driving-video audio is on-brand for that template (kid templates may want music off; dance-trend templates almost certainly want music on).
