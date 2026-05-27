---
name: Girl Dances row — white subjects, bake into chain prompt
description: For girl_dances templates, the Pattern-B swap subject should be a white/Caucasian woman; bake it into the chain prompt up front to avoid a second NBP pass
type: feedback
---

For the **girl_dances** template row, the Pattern-B swap subject should be a
**WHITE / Caucasian woman** (fair skin, light hair). User direction S80 ("we
only want white ladies"). Bake it into the per-template chain prompt's identity
clause **up front** so the first NBP edit lands it.

**Why:** the row's intended aesthetic; re-rolling the subject's ethnicity after
the fact costs an extra NBP pass (happened on Woman + Stateside before it was
baked into Like a G6).

**How to apply:** in `test_<slug>_chain.py`, the Pattern-B identity line should
say "a young WHITE / Caucasian woman with fair, light skin … light hair" rather
than "a skin tone different from the input." Wardrobe default = match the
source's register + coverage, change colors only; the user may direct
per-template specifics (Stateside: big clean-edged knee rips; Like a G6: gold
heels + nightlife regen). Per-template specifics live in the chain script
(preview only), never the generic runtime prompt
([[feedback_no_overfit_prompts]]). For a scene/lighting change the EDIT path
darkens the background but leaves the subject lit by the original light
(composited look) — use a **regen-framed** prompt instead
([[feedback_regen_vs_preserve_prompts]]).
