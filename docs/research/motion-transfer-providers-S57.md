# Motion-Transfer Provider Spike — Session 57 (2026-05-03)

**Goal:** Find a category-1 motion-transfer model (single character photo + driving video → animated character) for the Phase 2 wedge product. Source taxonomy: `memory/reference_motion_transfer_taxonomy.md`.

**Inputs used across all tests:**
- Character photo: `debug/Me.jpg` (286KB, near-square 849×871)
- Driving video: `debug/Dance_Video.mp4` (7.5MB, 1920×1080 @ 11.51s, dance choreography)
- Prompt (when prompt-driven): "person performs the exact dance from the reference video, identity preserved from the photo"

**Critical UX-outcome distinction discovered S57** (see `memory/reference_motion_transfer_two_outcomes.md`):

Within category-1 motion-transfer, two architecturally-similar products produce fundamentally different outputs:
- **Outcome 1 — character-into-scene:** swap the character in the driving video; preserve driving video's background. Pollo Wan 2.2 Animate `mix` does this. *"Put you in the video."*
- **Outcome 2 — motion-onto-character:** animate the character from user photo to perform the driving motion in user photo's setting. Swaptok + the user's main competitor do this (Swaptok poorly). *"You doing this motion."*

**Which outcome(s) the wedge should compete in is NOT yet decided** — and the answer may be "both." S57 user observation: the main competitor app ("AI Video") ships **both outcomes via different templates** against the same product. So outcome-selection is a template-level choice, not a product-level one. The Phase 2 template registry should encode `outcome` (1 or 2) per template and route to a model/mode that produces that specific outcome.

When testing future models, identify which outcome they produce so cost/quality comparisons stay apples-to-apples.

---

## Provider results

| Provider / model | Surface | Cost | Output specs | Quality verdict | Output artifact |
|---|---|---|---|---|---|
| **Higgsfield — Seedance 2.0** | MCP via Starter ($15) | n/a (geo-blocked) | n/a | **Eliminated.** Geo-blocked from US/Japan; only model in Higgsfield catalog with a `video` reference role. | n/a |
| **Higgsfield — Wan 2.6** | MCP via Starter ($15) | 38cr ≈ $2.85 | 1344×768, 15s, 720p | Not motion transfer (model architecturally takes only 1 image — no `video` role). Diagnostic gen only — Wan 2.6 is category-2 (prompt-driven I2V), not category-1. | n/a (consumed S57 sunk cost) |
| **Pollo — Wan 2.2 Animate (mix mode)** | Consumer web UI | 66cr × $0.05 = **$3.30 consumer / ~$4-5 API** | 1280×720, 11.467s, 4.2MB | "Not bad nor OMG fantastic" — mid. Single-shot, no prompt iteration. | `docs/research/Pollo_WanAnimate22_Mix_Output.mp4` |
| **Swaptok** (consumer app, name unknown beyond "Swaptok") | Mobile/web app | $3 | 944×960 square (cropped from 16:9 source), 11.467s, 11MB | **Failed.** Did NOT do motion transfer — instead tried to make user dance in their *own* background. Face out of frame for ~half the clip; background frozen. | `docs/research/Swaptok_Output.mp4` |
| **Viggle** | API key submitted ~2026-05-02 | n/a (key pending) | n/a | n/a (proven motion-transfer baseline; primary candidate when key arrives) | n/a |
| **Pollodance 2.0 Ref** (Pollo's flagship motion-transfer) | API only | n/a (API platform $80 minimum top-up not committed) | n/a | Not tested — quality unknown. Request body shape verified clean (validation passed; only blocker was credits). | n/a |
| **Kling Motion Control v2.6 — `image` mode (S58)** | Direct API (Singapore endpoint) | **8 cr × $0.14 = $1.12 / 10s gen** (post-trial); 100cr Trial pack free | 1424×1456 (~1:1, matches photo AR), 9.87s, 30fps, 22Mbps, 27.5MB. ~5min 53s gen time. | **Excellent — clean Outcome-2.** "Way better than Swaptok." Photo's background preserved. Fully recognizable dance. Character looks exactly like input photo. No glitches or frozen parts. | `docs/research/Kling_MotionControl_Image_Output.mp4` |
| **Kling Motion Control v2.6 — `video` mode (S58)** | Direct API (Singapore endpoint) | 8 cr × $0.14 = $1.12 / 10s gen | 1424×1456 (same as image mode — photo AR, NOT video AR), 9.97s, 30fps, 24.7Mbps, 30.8MB. ~7min 35s gen time. | **Failed — Swaptok-grade.** Same Outcome-2 (photo's background), but tried to graft full-body dancer's pose onto headshot input → character half-out-of-frame, motion misaligned. **Not Outcome-1.** | `docs/research/Kling_MotionControl_Video_Output.mp4` |

---

## Cost data points

| Source | Per-credit cost | Per-gen cost (this test) |
|---|---|---|
| Higgsfield Starter | $15/200cr = $0.075 | Wan 2.6: $2.85 |
| Pollo consumer subscription | $15/300cr = $0.050 | Wan 2.2 Animate (mix): $3.30 |
| Pollo API platform (estimated) | $80/1333cr = $0.060 (bulk) | Wan 2.2 Animate equivalent: ~$3.96 |
| Swaptok consumer | n/a (per-clip) | $3.00 |
| **Kling API (post-trial, S58)** | **$0.14 / cr** (user-confirmed) | **Motion Control 10s Pro: $1.12** |

**Real market price point: ~$3-5 per motion-transfer clip** (Swaptok charges $3 for a failed result; Pollo $3.30 for a mid result). Kling at **$1.12 COGS for clean Outcome-2** opens room for a $2-3 retail wedge with healthy margin — the earlier "wedge target $1-2 retail" intuition is back on the table once we factor in clean-quality COGS, not the failed/mid-quality competitor pricing.

---

## Surface-billing finding (general, not provider-specific)

Multiple providers split their billing into **consumer pool** and **API platform pool**:

- **Pollo:** explicit on their dashboard — *"API credits and user credits operate independently and are not interchangeable."*
- **Higgsfield:** free-plan balance shown but video-gen blocked — separate entitlement model.

Implication: a paid consumer subscription does NOT fund API calls. For provider evaluation, ALWAYS probe the exact code-path/surface the production integration will use — not the surface the user has credits on. Captured in `memory/feedback_balance_neq_entitlement.md`.

---

## UX patterns observed (worth saving for Phase 2 design)

- **Swaptok's input pattern:** "Upload a photo and paste a TikTok/Instagram link" — driving video is *referenced by URL*, not *uploaded as a file*. Mobile-native: user taps share-sheet from TikTok → app extracts the video. Far less friction than "upload a 7MB MP4 from your camera roll."
- **Pollo Mimic's mode picker:**
  - `move` = animate a still image with realistic motion = category-2 prompt-driven I2V
  - `mix` = replace a character in an existing video = category-1 motion transfer
  - Wan 2.2 Animate has BOTH modes under one model ID — the `mix` variant is the only one that belongs in category 1 of the taxonomy.

---

## S57 verdict & next moves

**Eliminated:**
- Higgsfield (Seedance geo-blocked from US; Wan 2.6 is wrong category)

**Tested, parked (B-team if Viggle disappoints):**
- Pollo Wan 2.2 Animate `mix` — outcome-1 product, mid quality at $3.30 consumer / ~$4 API per gen. Fair candidate for an outcome-1 wedge if we go that direction.
- Pollodance 2.0 Ref (untested; would require $80 API commit + outcome verification — could be outcome 1, outcome 2, or even hybrid).

**Worth re-testing at Pollo without API commit:** other Pollo Mimic models (Bytedance Imitator, Runway Act-2, Kling 3.0 Motion Control with Subject Binding, or Wan 2.2 Animate's `move` mode) — find one that produces outcome 2 cleanly. Same consumer-credit cost (~$3 ish per gen), gives us an apples-to-apples Pollo-on-outcome-2 datapoint to compare against the outcome-1 mix test.

**Pending:**
- **Viggle** (key submitted ~May 2; proven motion-transfer baseline; primary candidate).
- At Viggle's first spike, **explicitly identify which outcome it produces** before declaring a quality verdict — don't assume from marketing copy.

**When Viggle key arrives:** repeat this exact spike (same selfie + same dance video) so the comparison is apples-to-apples — but ALSO label which outcome Viggle's output represents. Add a row to the table above. The wedge-outcome decision is downstream of having both outcome-1 AND outcome-2 quality+cost data points across at least 2 providers each.

**Open questions deferred:**
- Real market price ceiling for this product category — $3 is one data point, need 2-3 more to triangulate.
- Whether prompt-tuning or a different Pollo Mimic model (Bytedance Imitator, Runway Act-2, Kling 3.0 Motion Control with Subject Binding) could push Pollo from "mid" to "good" — only worth revisiting if Viggle disappoints.

---

## S58 update (2026-05-05/06) — Kling Motion Control spike + outcome strategy locked

**Result: Kling Motion Control v2.6 is the V1 Outcome-2 provider.** Spike inputs identical to S57 (`debug/Me.jpg` + `debug/Dance_Video.mp4` trimmed to 10s, uploaded to `https://files.catbox.moe/xwiktk.mp4`). Two runs at `pro` mode, both modes of `character_orientation`. Both rows added to the provider table above.

### Critical finding — provider mode names ≠ outcome names

I assumed Kling's `character_orientation: image` and `character_orientation: video` would map to Outcome-2 and Outcome-1 respectively. **Wrong.** Both modes produce **Outcome-2** (photo's background, photo's framing). The toggle controls *character orientation/pose within a photo-AR frame*, not which background wins.

- `image` mode: clean win — preserves photo framing AND animates the character with the reference dance. **This is the V1 path.**
- `video` mode: tries to graft the reference video character's pose onto the input photo. With our headshot input + full-body dance video, this produced a Swaptok-grade failure (head-only, half out of frame). Even with a matching full-body input photo, it would still produce Outcome-2 — just differently composed. **Narrower applicability AND higher failure surface than `image` mode.**

Saved as memory `feedback_provider_mode_names_neq_outcomes.md`. Recall before any future provider spike.

### V1 outcome strategy — both locked, single-provider architecture

| Outcome | V1 pipeline | Status |
|---|---|---|
| **Outcome 2 (user in user's scene)** | **Kling 2.6 Motion Control, Pro mode, `image` orientation** (selfie + ref video → output) | **LOCKED.** $1.12 COGS @ 10s, ~5-6min latency, clean quality. |
| **Outcome 1 (user in template's scene)** | **Nano Banana Pro Edit (v4 holistic-regen prompt) → Kling 2.6 Motion Control, Pro mode, `video` orientation** (selfie + ref video first frame → regen frame; regen frame + ref video → output) | **LOCKED.** $0.04 + $1.12 = **$1.16** COGS @ 10s, ~7-8min latency, clean quality verified. |

**Single-provider architecture.** Both outcomes route through Kling backend with one Nano Banana pre-step for Outcome 1. Pollo is officially OFF the V1 plan (no $80 API top-up needed). Client scaffolded: `src/speech_to_video/clients/kling_motion_client.py`. Nano Banana Pro Edit already wired via `AIMLAPIClient`.

### Outcome-1 input-shaping spike — abandoned at v3, unlocked at v4 (S58)

**Hypothesis:** since Kling preserves the photo's background, feed Kling a *pre-shaped photo* (the dance video's first frame with the user's identity placed in the dance scene) and Kling will produce Outcome 1. Source: Aakash Gupta's tweet. Pre-step uses Nano Banana Pro Edit (already in our stack).

**Four prompt iterations of the pre-step:**
- **v1 — "swap the face, keep everything":** structural Outcome 1 ✓ (1936×1072, dance scene preserved), face fidelity broken: dancer's sunglasses contorted user's face; dancer's skin tone on visible hands/arms broke identity continuity; user verdict — "experience ruined."
- **v2 — "remove sunglasses + match skin tone everywhere":** introduced its own bug — would also strip accessories the user wears in their selfie. Caught before run.
- **v3 — accessories-follow-second-image rule:** clean swap (sunglasses gone, face matches user, skin tone consistent, pose/clothing/background preserved). But the resulting video still felt paste-in: face lighting didn't match scene lighting. Initial conclusion: "model-class ceiling, switch to Pollo `mix`." Saved as memory.
- **v4 — holistic regen reframing (after `Match Video` digression):** instead of "preserve everything, change face/identity," reframe as *"regenerate a coherent photograph: take pose/scene/lighting/dimensions from image-1 (dance frame), take identity AND clothing from image-2 (selfie), naturally imagine body parts not visible in image-2 (e.g. lower body in user's clothing style), DO NOT preserve image-1's character/clothing/face."* The regen frame was clean (`https://cdn.aimlapi.com/generations/openai-image-generation/1778130248563-18eded90-e2f8-4f36-922f-69aa01cb8301.png`). Final video: clean Outcome 1, user's identity in dance scene, motion preserved, lighting integrated. **User verdict: "Wow, this is gold."**

**The architectural lesson — corrected.** v3's failure looked like a model-class ceiling (localized-edit model can't do holistic integration). v4 proved the same model CAN do holistic integration when the *task is reframed in the prompt*. v3 told Nano Banana to be conservative ("preserve everything except face" → produces localized edit + paste-in lighting). v4 gave it latitude ("regenerate the entire character holistically combining elements A and B" → produces holistic regen + integrated lighting). Same model, same endpoint, same inputs — fundamentally different output behavior.

**Updated rule (memory amended):** `feedback_localized_edits_cant_holistic_regen.md` rule was too absolute. Corrected: try BOTH a localized framing AND a regen framing on the same model before declaring a model-class ceiling. New related memory: `feedback_regen_vs_preserve_prompts.md` captures the prompt-framing distinction itself.

**Spike artifacts:**
- v1 swap output: `https://cdn.aimlapi.com/generations/openai-image-generation/1778117558661-3eff0123-3e18-461d-b8ed-f5c1d2ab6f13.png`
- v1 final video: `docs/research/Kling_Outcome1_Output.mp4` (44MB, structural Outcome 1, broken face)
- v3 swap output: `https://cdn.aimlapi.com/generations/openai-image-generation/1778120906107-6514a9ea-94d0-498b-9647-f916768fe0f8.png` (clean swap, never run through Kling — Kling on this v3 frame would have inherited the same paste-in lighting)
- v4 regen frame: `https://cdn.aimlapi.com/generations/openai-image-generation/1778130248563-18eded90-e2f8-4f36-922f-69aa01cb8301.png`
- **v4 final video (the result that locked Outcome 1): `docs/research/Kling_Outcome1_Regen_VideoMode_Output.mp4`** (33MB, 1936×1072, 9.97s, ~$1.16, ~8min total)
- Spike script: `scripts/kling_outcome1_spike.py` (supports `KLING_RUN_STEP=swap_only|full`, `KLING_ORIENTATION=image|video`, `SWAPPED_URL=<cached>` to avoid Nano Banana re-cost between Kling iterations)

**Cost burned on Outcome-1 spikes:** ~$0.12 (3× Nano Banana Pro Edit calls — v1, v3, v4) + 16 trial Kling credits ($0 actual). Final pipeline COGS is $1.16/gen at production rates.

**Implications now that both outcomes are locked on Kling:**
- **Phase 2 scaffolding can proceed.** Single backend client (`kling_motion_client.py`) + a Nano Banana pre-step for Outcome-1 templates. Single trust boundary, single billing surface.
- **Pollo `mix` is officially off the V1 plan.** $80 minimum API top-up no longer needed.
- **Viggle still de-prioritized.** Already decided pre-v4; the v4 result reinforces (no second-source urgency for Outcome 2 either, given Kling delivers cleanly at $1.12).
- **Variance testing still needed before production confidence.** v4 was ONE test on ONE selfie + ONE dance video. Different selfies (full-body, different lighting), different reference videos (non-dance content), different framing combinations need to be tested before declaring "production-ready." Cheap to test on remaining trial credits or post-trial.

### Cost notes

- Trial pack: 100cr free, 1-month expiry, 5 concurrent jobs.
- Confirmed via `GET /account/costs` — auth/JWT works on account endpoints too, not just generation.
- Post-trial rate: $0.14/cr (user-confirmed). Per-gen at 10s `pro`: 8 cr × $0.14 = **$1.12**.
- 12 generations remaining on trial pack at this rate (84 cr left after 2 gens).
- Note from doc: `remaining_quantity` has up to 12h delay — for ledger reconciliation purposes don't trust it as authoritative.

### Open questions still deferred

- Real market price ceiling — Kling at $1.12 COGS has reset the wedge math. $2-3 retail target now feasible with healthy margin.
- Latency UX: 5-6 min for Outcome-2 is at the edge of acceptable for "tap and wait" — copy/expectation-setting in mobile UI must under-promise. Better than under-promising 5min on Hailuo-S2V (which actually returns in 30-60s) — Kling's promise will need to be "5-10 min" or "a few minutes" to absorb tail latency.
- Real photo input distribution for V1: our test was a near-square 849×871 user selfie. We've not yet tested portrait-9:16, landscape-16:9, or full-body inputs through Kling. Worth one more spike to see how aspect ratio is handled before scaffolding mobile photo picker constraints.
