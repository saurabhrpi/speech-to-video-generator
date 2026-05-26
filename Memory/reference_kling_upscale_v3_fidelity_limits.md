---
name: kling-upscale-v3-fidelity-limits
description: Don't reach for driver-upscale or Kling v3 to fix camera-motion or fast-transition jumps. A sharper driver transfers BOTH wanted detail AND unwanted source camera motion; v3 ≈ v2.6 on motion fidelity (2× cost). These are source-property / interpolation limits, not resolution/model levers.
metadata:
  type: reference
---

# Upscale + v3 don't fix Kling motion-fidelity issues (S79 Give It Up)

When a Kling Motion Control output has a motion-quality flaw, **driver-upscale and v3 are the wrong levers** for most of them. What each actually does:

- **Driver upscale (Topaz 2k) → more *faithful* transfer of EVERYTHING.** It sharpens detail (hands improved on Give It Up — the one win) but ALSO amplifies **unwanted source motion**: Give It Up's source was a handheld phone that lowers, and the 2k driver made the camera-lowering ~10% MORE evident (the soft driver blurred it enough that Kling under-tracked it). So upscale is a tradeoff, not a pure win — only reach for it when the flaw is *softness/detail* (hands, face), and expect any source camera drift to come through harder. (Static camera is still Kling's one hard driver requirement — [[kling-driver-quality-checklist]].)
- **Fast pose-transitions read jumpy** ("missing-frame" feel on a quick hands-joined→gesture move) = Kling's **interpolation limit** on fast motion. Per-gen stochastic but can be inherent to that transition. NOT resolution-driven.
- **v3 ≈ v2.6 on motion fidelity.** A/B on the identical driver+image: v3 did NOT fix the jumpy transition and did NOT reduce the camera-lowering (in fact its lowering read as "pressing the face down"). v3's wins are facial consistency + longer cap (see [[kling-v3-model-string-and-cost]]), NOT motion smoothness — and it's ~2× cost. **Do not flip to v3 hoping to smooth a transition or fix camera motion.**

## What to actually do

- Flaw is **soft hands/face** → upscale the driver (Topaz, [[topaz-video-api]]), accept that source camera drift comes through harder.
- Flaw is **camera drift/lowering** → it's in the source (static-camera requirement); upscale makes it worse, v3 doesn't help. Accept it, pick a stiller source, or stabilize the driver.
- Flaw is a **jumpy fast transition** → re-roll (stochastic) is the only cheap lever; if it recurs it's inherent — accept or move on. v3 won't fix it.

Cost of learning this: ~$6 of Give It Up rolls (soft-driver → 2k → v3) before concluding the 2k/v2.6 take was the keeper (jumpy transition accepted).
