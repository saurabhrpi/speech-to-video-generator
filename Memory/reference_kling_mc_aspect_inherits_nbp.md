---
name: kling-mc-aspect-inherits-nbp
description: CONFIRMED (S73) — Kling MC inherits the input character image's aspect ratio. 1024×1024 NBP edit → 960×960 Kling output verified end-to-end on Thriller (task 886680218651066459, succeeded 14.93s). Wide-arms T-pose NBP prompt is the canonical recipe for forcing 1:1 Kling output when source video is portrait.
metadata:
  type: reference
---

**✅ VERIFICATION STATUS (S73):** End-to-end confirmed. Thriller NBP edit at 1024×1024 (wide-arms T-pose) → Kling v2.6 + std + video + 15s produced **960×960** output (perfect 1:1). The rule below is now load-bearing canon for V2 template prep.

**The hypothesis:** `NBP input AR → NBP output AR → Kling output AR`. Kling MC faithfully inherits the input character image's aspect; everything else (orientation, mode, model version) is downstream noise.

**S72 evidence (Thriller debug):** five Kling runs all gave portrait 9:13.5 output (784×1168 std, 1184×1760 pro) because the NBP edit was 848×1264 (portrait). Five hypothesis-then-fail tests:
- v3 + std + image + 10s → 784×1168 portrait (theory: image-orientation gives wide — wrong)
- v3 + pro + image + 10s → 1184×1760 portrait (theory: pro gives ~1:1 — wrong)
- v3 + std + video + 15s → 784×1168 portrait
- v2.6 + std + video + 15s → 784×1168 portrait (theory: v2.6 always outputs ~1:1 per S58 — wrong; S58 was just coincidence of NBP inputs being ~1:1)

The fix: re-NBP with wide-arms T-pose prompt → produced **1024×1024 perfect 1:1**, which then forces Kling to output 1:1.

**Why past Pipeline A templates were ~1:1:** all of them used cropped competitor-app PNGs (~1284×1250, AR ~1.03) as NBP input. Verified S72:
- baby_dance_edit.jpg: 1075×992 (AR 1.08)
- beat_it_edit_188eaa32.jpg: 1052×1024 (AR 1.03)
- bad_edit_78d0a6e9.jpg: 1052×1024 (AR 1.03)
- gangsta_edit.jpg: 942×1136 (AR 0.83)
- Smooth Criminal NBP edit similar; Kling output was 1456×1424 (~1:1)

**The wide-arms T-pose trick (S73 confirmed end-to-end):** prompt NBP with "subject in T-pose with both arms extended WIDE to the sides, palms forward, full wingspan visible, frame MUST accommodate full arm span with room on both LEFT and RIGHT sides — square or near-square aspect (1:1)." Gemini composes a 1024×1024 frame to fit the wingspan. Kling MC then inherits that, producing 960×960 (verified on Thriller v2.6+std+video+15s). Reusable for any V2 template where the input source is portrait and we want Kling output to have lateral room.

**Why this matters:** without controlling NBP edit aspect, Kling's output is locked to whatever NBP produced — which itself drifts based on input PNG aspect. Past templates worked because we always cropped to ~1:1 before NBP. New templates fed uncropped portrait sources (like Thriller's original Thriller.png at 1284×1718) will give portrait Kling output unless we explicitly steer NBP composition.

**⚠️ Caveat — 1:1 is necessary but NOT sufficient (S73 eyeball):** Even with a perfect 1:1 NBP edit, Kling can still clip a hand/leg out of frame in a few moments if the **driving video's camera does not follow the dancer**. Aspect ratio controls the canvas; whether the dancer stays centered inside that canvas is governed by camera tracking in the driving video. Thriller S73 output (960×960 from 1024×1024 NBP) had 2 brief out-of-frame moments because the driving video's camera was static while the dancer drifted laterally. For non-chopped output start-to-end, BOTH conditions must hold: (1) ~1:1 NBP edit AND (2) driving video where camera tracks the dancer to keep them centered.

**How to apply:** Pre-template prep step — verify the NBP edit's aspect ratio matches what you want Kling to output. If aspect drift, either re-NBP with composition-steering pose prompt, or Pillow-resize the NBP edit before R2 upload (less reliable; NBP's natural composition is the cleaner fix). Separately, evaluate the driving video for camera tracking — a static-camera source with a laterally-moving dancer will produce chopped limbs even with a 1:1 character image. See related: [[regen-vs-preserve-prompts]], [[nbp-wont-remove-ui-overlays]], [[kling-driver-quality-checklist]].
