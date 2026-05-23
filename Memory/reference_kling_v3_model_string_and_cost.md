---
name: kling-v3-model-string-and-cost
description: Correct model_name string for Kling v3 on the direct Motion Control API is "kling-v3" (NOT "kling-v3-0" which third-party wrapper docs claim — Kling rejects it with error 1201). Cost is ~2x v2.6 at the Kling-side API level.
metadata:
  type: reference
---

**Correct value:** `model_name="kling-v3"` on Kling's direct API (`https://api-singapore.klingai.com/v1/videos/motion-control`).

**Wrong values that wrapper docs claim** (and Kling's direct API rejects with error 1201):
- `"kling-v3-0"` (Eachlabs docs say this; rejected)
- `"kling-v3-motion-control"` (ModelsLab docs say this; not tested but likely wrapper-specific)
- `"kling-v3.0-motion-control"` (Vercel AI Gateway; wrapper-specific)
- `"kling-3.0/motion-control"` (Kie.ai; wrapper-specific)

Each third-party wrapper invents its own naming. Only `kling-v3` works against Kling direct.

**Cost (S72 measured, Kling-side only — does NOT include NBP / R2 / our retail markup):**
- v2.6 + pro + image + 10s ≈ **~$1.02 per gen**
- v3 + std + video + 15s ≈ **~$2.00 per gen** (~2x v2.6 despite std mode and lower res)
- Variables in play: model version is the dominant cost driver. std vs pro is a smaller lever within a model. Duration scales but not linearly.

**Pros of v3 (vs v2.6):**
- Better facial consistency (per Kling marketing + Replicate docs)
- Same endpoint shape — drop-in replacement at the API level
- No reliable speed advantage observed (S72 sample: v3 avg 4.9 min, v2.6 avg 4.6 min)

**Cons:**
- ~2x cost at Kling-side
- v3's output aspect inherits the NBP edit's aspect more aggressively (see [[kling-mc-aspect-inherits-nbp]])

**Revert path:** client default at `src/speech_to_video/clients/kling_motion_client.py:72, 148` — single-line change `"kling-v3"` → `"kling-v2-6"`. Class docstring explains the trade-off explicitly.

**How to apply:** If you're spending Kling credits on a template that doesn't have a face-quality complaint, use v2.6 explicitly. If face artifacts are the visible failure mode, try v3 — but factor the 2x cost into COGS math. Default stays v3 until real-user data shows v3's lift doesn't justify the cost. See related: [[kling-mc-aspect-inherits-nbp]].
