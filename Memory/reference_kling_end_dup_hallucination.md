---
name: kling-end-dup-hallucination
description: Kling MC tends to hallucinate a DUPLICATE of the subject near the END of longer clips (~14.5s onset on Beat It, recurring across rolls). Re-rolling doesn't reliably avoid it. Mitigate upstream (NBP composition-lock) + downstream (trim the tail before onset).
type: reference
---

Kling Motion Control tends to hallucinate a **duplicate of the subject** (a second copy of the dancer) near the **END** of longer clips.

**S76 Beat It evidence:** the duplicate appeared with onset ~**14.5s** across MULTIPLE separate rolls — on both a 15.4s output (full driver) and a 14.9s output (0.5s-cropped driver, different NBP edit) — and a faint ghost was already forming *right at* 14.5s before it became obvious. So it **recurs across re-rolls** — re-generating does NOT reliably dodge it.

**Likely cause:** the same camera-approach / subject-zoom motion trigger called out in the runbook's NBP composition-lock note (`docs/V2_template_creation_runbook.md` step 4) — the driving video's end motion makes Kling spawn a second subject.

**Mitigations:**
- **Upstream:** NBP composition-lock in the edit prompt — "subject occupies the SAME frame proportion as the input, do NOT zoom in/out, preserve camera-to-subject distance." Runbook step 4.
- **Downstream:** cap/trim the clip tail BEFORE the dup onset. Cap a hair *earlier* than the visible onset (e.g. ~14.3s, not 14.5s) since a faint ghost forms slightly before it's clearly visible.

S76: this (plus the per-gen-variable audio lead, see [[kling-audio-lead-and-preview-propagation]]) is why the Beat It preview rebuild was abandoned and the prod version retained. Related Kling failure modes: [[moving-overlays-degrade-kling]], [[kling-driver-quality-checklist]].
