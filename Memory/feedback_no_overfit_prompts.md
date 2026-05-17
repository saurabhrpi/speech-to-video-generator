---
name: no-overfit-prompts
description: ⚠️ PROMPTS MUST BE GENERIC. Specifics for one user/template/case go in per-row config, not in the prompt core. Overfitting is treated the same as overfitting in ML.
metadata:
  type: feedback
---

# ⚠️ DO NOT OVERFIT PROMPTS ⚠️

**Rule:** Prompt strings written into the codebase (or into a default prompt template) MUST be generic across every legitimate input the pipeline will ever see. Anything specific to one user, one template, one wardrobe, one scene, one body framing, one language register → does NOT belong in the prompt core. It belongs in **per-row config** (Firestore template fields, request overrides, dispatched parameters).

The user calls this overfitting and means it in the ML sense. Overfit prompts will pass the spike test on the one case they were written for, then degrade quality on every other case in the dataset.

## Concrete failures from S66 (don't repeat these)

I wrote both of these in the same session. Both are wrong.

❌ `"...if the lower garment or footwear is not visible, infer them as full-length traditional garments matching the upper-body attire — do NOT introduce dance shorts, athletic wear, or generic dancewear."`
- Overfit: assumes the input is traditional Indian wear (or anything with conservative full-length lowers). Fails immediately if the next user is wearing jeans + a t-shirt, where shorts/athletic wear would actually be coherent. Also baked in a *negation* (`do NOT introduce shorts`), which means a future "Beach Vibes" template that wants shorts gets actively sabotaged.

❌ `"Composition: full body standing pose, head to feet."`
- Overfit: assumes the template's driving video is a standing dance shot. Fails on a sitting-pose template, a waist-up close-up template, an upside-down stunt template, a portrait-frame template.

## The architectural pattern that fixes this

Separate prompts into two layers:

1. **Generic core** (lives in code): describes the *operation*, not the *content*. Examples from S66 NBP regen step:

    > *"Generate a more complete portrait of this person. Preserve facial identity, hair, and the visible clothing style. Extrapolate any non-visible body parts, garments, and footwear in a way that is stylistically continuous with what is visible."*

    No mention of Indian, jeans, standing, sitting, shorts, dancewear, full-body, head-to-feet, or any other content-specific term. Just the *task*: regen, preserve identity + style, extrapolate stylistically.

2. **Per-template hint** (lives in Firestore template row, e.g. `template.nbp_framing_hint`): the framing/content specifics for *that one template*. Bombale gets `"Composition: full body standing pose, head to feet"`. A torso-only template gets something else, or nothing. The dispatcher concatenates `{generic_core}\n\n{per_template_hint}` at request time.

## How to apply

Before writing a prompt string, ask:
- Will this read coherently across **every** legitimate input to the pipeline?
- If a future user/template/case violates a baked-in assumption (wardrobe, pose, framing, language register, cultural context), does the prompt break?
- Am I about to write a *negation* (`do NOT do X`) — and is X actually wrong for every case, or just wrong for the one I'm testing?

If you can name even one realistic input that the prompt would degrade, it's overfit. Move the specifics to per-row config.

Related: [[prompt-fixes]] (same family of issues — when *not* to wordsmith a prompt at all).
