---
name: Viggle is a proprietary model, not a wrapper
description: Viggle's V4_Preview / V3_Preview are their own motion-transfer models — NOT a thin wrapper over Kling/Seedance. No underlying-model bypass exists to cut Viggle's pricing
type: reference
---

Viggle's API exposes `model: V4_Preview` (default) or `V3_Preview` (legacy) — these are Viggle's own purpose-trained motion-transfer models. They are NOT a wrapper over Kling, Seedance, or other generic I2V providers. Viggle's core IP is their motion-transfer-from-driving-video architecture.

**Why this matters:** the intuitive assumption ("Viggle is just a UI on top of cheaper models, let's call those directly") is wrong. There is no underlying model we can hit to undercut Viggle's pricing. To beat Viggle on cost, you have to use a *different* model with *different* tradeoffs (Higgsfield, Wan 2.2 Animate, Bytedance Imitator) — not bypass Viggle.

**Architectural distinction (root of the confusion):**
- Generic I2V models (Kling, Seedance, Sora, Veo, Hailuo I2V) take image + TEXT PROMPT describing motion. They cannot accept a driving video as the motion source.
- Motion-transfer models (Viggle, Higgsfield, Wan 2.2 Animate) take image + DRIVING VIDEO and transfer the video's motion onto the character. Different model class, different training data.

**Pricing reference (May 2026):** Viggle on-demand = 1 credit/sec of output video. Preprocessed scenes free; preprocessed characters cost 1 credit. USD/credit pricing requires login at portal.viggle.ai.

**API modes (from docs.viggle.ai):**
- `On-Demand`: send image + driving video in one render call
- `Preprocessed`: preprocess character (1cr) + scene (free) once, then render with IDs (~3x faster at scale)
- `Import Templates`: skip uploading a driving video — reference Viggle's public template_id from viggle.ai instead
