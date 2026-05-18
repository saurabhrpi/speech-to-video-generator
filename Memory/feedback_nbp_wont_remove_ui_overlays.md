---
name: nbp-may-fail-on-ui-overlays
description: Nano Banana Pro Edit sometimes refuses to remove baked-in UI overlays (X buttons, caption bars) — works on some inputs, fails on others. If it fails twice in a row, stop iterating on the prompt and pre-crop the input.
metadata:
  type: feedback
---

When the input image has app-UI overlays baked into the pixels (e.g. a screenshot of a template card with an X close-button in the corner + a black caption strip at the bottom), `gemini-3-pro-image-preview` Edit's success rate on removing them is **inconsistent**:

- **S67 Gangsta** — `gangsta_reference.png` had X button + caption strip → first NBP run with a standard "Remove the X button. Remove the dark gradient at the bottom..." prompt stripped both cleanly. One attempt, done.
- **S67 Baby Dance** — `Baby dance.png` had the same overlay shape → first NBP run retained both overlays. Second run with much more emphatic prompt ("SOLID BLACK BAR covering bottom 1/6 ... MUST be removed") regenerated the rest of the image dramatically (outfit + pose drifted) BUT still kept the X + caption. Third approach: pre-crop the input with Pillow (drop bottom 19%, mask top-left 220×220 with a sampled neighbor color) before passing to NBP — worked first try.

Same model, same prompt shape, same input format (PNG screenshot from the V2 template card UI). Why one worked and one didn't is unclear — possibly image complexity (Baby Dance has a busy dollhouse + TV in the bg) or pixel coverage (the Baby Dance caption strip is taller). Could also just be model variance.

**How to apply:**
- First attempt: just ask NBP to remove the overlays as part of the edit prompt. It might work.
- **If it fails once, don't retry with a stronger prompt** — the second attempt at Baby Dance gave a worse output overall (dramatic regeneration + still retained overlays). Wasted ~$0.10 + 40s.
- Fallback: pre-process the input with Pillow before passing to NBP. Crop the offending region (e.g. `img.crop((0, 0, w, int(h*0.81)))`) or mask it with a sampled neighbor color. NBP then handles the remaining edit cleanly. For an X-button corner: 220×220 mask was enough on a 1284-wide source; 110×110 wasn't (the button extends past 100px).
- See `scripts/test_baby_dance_chain.py` for the working pre-crop approach.
