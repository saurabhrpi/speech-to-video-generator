---
name: Motion-transfer has two distinct UX outcomes (within category-1)
description: "Single photo + driving video → animated video" splits into two fundamentally different products: character-into-scene (preserve driving video's setting) vs motion-onto-character (preserve user photo's setting). Schemas look identical; products are different.
type: reference
---

Within the category-1 motion-transfer space (see `reference_motion_transfer_taxonomy.md`), there are two distinct UX outcomes that look architecturally identical at the API level (both take a photo + driving video and return a video) but produce fundamentally different end products. Picking the wrong one for the wedge means competing in a different market than intended.

**In BOTH outcomes the user-character performs the template's (driving video's) motion.** The split is about *which scene wraps that motion*, not who's moving — both put YOU doing the template's motion. Don't let the "swap vs animate" mechanical naming obscure that.

**Outcome 1 — User in the template's scene** (template-scene wins):
- The output preserves the **driving video's background**, lighting, framing, secondary characters. User character replaces the original performer.
- User-facing value prop: *"Be in scenes you couldn't be in IRL"* — celebrity stages, action-movie hallways, music-video sets, viral moments. **The scene's specificity is the point** — the iconic location/lighting/context is what makes the content shareable.
- Best for templates where the *setting* is part of the joke / brand / hook (recognizable backdrops, branded environments, dramatic lighting setups).
- Verified surfaces: **Pollo Wan 2.2 Animate `mix` mode** (S57, `docs/research/Pollo_WanAnimate22_Mix_Output.mp4`); main competitor's "AI Video" app on certain templates (S57 user test).

**Outcome 2 — User in user's own scene** (photo's scene wins):
- The output preserves the **user photo's background**, setting, framing. The character from the photo is animated to perform the driving video's motion in the photo's own context.
- User-facing value prop: *"Believable that I shot this myself"* — personal-content authenticity, "me in my room doing X." The intimacy and authenticity of the user's own setting is the point.
- Best for templates where the *motion* is the hook and the setting is interchangeable (dance challenges, gestures, expressions — content that works in any setting).
- Verified surfaces: **Kling Motion Control v2.6 `image` mode** (S58, clean — `docs/research/Kling_MotionControl_Image_Output.mp4`); **Swaptok** (S57, executed badly — `docs/research/Swaptok_Output.mp4`); main competitor's "AI Video" app on other templates (S57 user test). Likely some Viggle modes — confirm at first Viggle spike.

**Critical S57 observation: outcome is a TEMPLATE-LEVEL choice, not a product-level one.** Same competitor product ("AI Video") ships both outcomes — different templates produce different outcomes against the same engine selection. Implication for our wedge: the Phase 2 template registry should encode `outcome` (1 or 2) per template, and route to a model/mode that produces that specific outcome. Don't pick an outcome for the whole product — let each template pick.

**Why this matters for provider evaluation:**
- API schemas don't disambiguate the two outcomes — both look like `{image, video} → video`. You only learn which outcome a provider does by running it (or by reading marketing copy carefully — "put you in the video" = outcome 1; "you do this motion" = outcome 2).
- The two outcomes appeal to different consumer impulses. Choose based on which our wedge thesis depends on.
- A provider may offer EITHER mode (single product), or BOTH as separate modes (Wan 2.2 Animate has `mix` for outcome 1; check whether `move` or other modes do outcome 2 on Pollo's Mimic surface).

**How to apply:**
1. Before judging a motion-transfer provider, identify which outcome the test produced. Don't conflate outcome-1 results with outcome-2 results in cost/quality comparisons.
2. When asking the user which provider to spike next, ALSO ask which outcome the wedge needs — and remember the answer may be "both, on different templates."
3. Frame the test prompt and inputs around the target outcome — same selfie + driving video can produce either outcome depending on the model/mode selected.
4. Phase 2 template registry: every template entry should declare its `outcome` (1 or 2) and route to a model/mode that delivers that outcome cleanly. Don't pick a single outcome for the whole product.
