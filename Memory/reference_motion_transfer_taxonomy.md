---
name: Motion-transfer model taxonomy (2026)
description: Three distinct AI-video-from-photo categories often confused — motion-transfer-from-driving-video, prompt-driven I2V, and face-animation — each has different best-fit models and wrong picks kill product fit
type: reference
---

Three categories of "AI video from a photo" that look similar but use entirely different model classes. Picking the wrong one wastes integration time:

**1. Motion-transfer-from-driving-video** (subject performs a motion sourced from a reference video):
- Inputs: 1 character photo + 1 motion reference video → character does that motion
- Best for: dance, action ("user does Bombale"), full-body templates
- Models: **Viggle** (proprietary V4/V3_Preview), **Pollo Mimic** (aggregator UI: Wan 2.2 Animate + Bytedance Imitator + Runway Act-2), **Bytedance Seedance** (has a `video` reference role — accessible directly OR via aggregators like Higgsfield; empirically unverified for true motion transfer), open-weights **Wan 2.2 Animate**, **Higgsfield** (catalog changes — verify current models before assuming any specific product name)
- Note on tag-vs-behavior mismatches: providers may tag prompt-driven I2V models as "motion-transfer" in marketing copy. Always verify the model accepts a driving-video input role (not just `start_image`/`end_image`) before classifying it as category 1.

**2. Prompt-driven I2V** (animate a still photo from a text prompt):
- Inputs: 1 photo + text describing motion → animated photo
- Best for: VFX transformations ("become a mermaid", "skydiving"), generic animation
- Models: **Veo 3 Fast** (Google, what reference "AI Video" app uses for VFX templates), **Kling**, **Sora 2**, **MiniMax Hailuo I2V**, **Pika**, **Luma Dream Machine**

**3. Face-animation / talking-head** (still face becomes a speaking/emoting head):
- Inputs: 1 face photo + audio (or short forward-facing driving video, face only) → talking head
- Best for: portrait animation, lip-sync, "make this person speak"
- Models: **D-ID**, **HeyGen** (paid easy); **LivePortrait**, **SadTalker**, **Wav2Lip** (open-source DIY)

**Wrong-category mistakes to avoid:**
- Kling/Sora/Veo are NOT motion-transfer — they take prompts, not driving videos. Don't pitch them for "user does Bombale."
- Viggle/Higgsfield need a driving video — don't pitch them for "become a mermaid."
- D-ID/HeyGen are face-only — never full-body.
- **Runway Act-One** is a special case: motion-transfer-shaped API but its driving video must be **forward-facing with minimal body and head movement** — face-driven only. Fails for full-body dance.

**For our app (template-grid product):** dance/action rows = category 1; VFX rows = category 2; future "make anyone speak" rows = category 3. Backend template registry needs a `model` field per template to route correctly to the right engine.
