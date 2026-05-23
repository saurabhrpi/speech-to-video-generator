---
name: nbp-cant-reposition
description: NBP (gemini-3-pro-image-preview via Google AI Studio direct) cannot reliably perform RELATIVE-POSITION edits — "move subject smaller / shift in frame / push farther into scene" produces near-identical output. The model anchors to the input's composition no matter how aggressive the prompt. Workaround: AIMLAPI nano-banana-pro-edit (different model, better at composition shifts but aspect-inconsistent) OR manual Photoshop.
metadata:
  type: feedback
---

**Rule:** Don't waste iterations asking NBP to "make the subject smaller" / "push the subject farther into the scene" / "shift the subject up by N pixels". The unified Gemini 3 Pro image model (`gemini-3-pro-image-preview`) anchors to the input frame's compositional register and won't move the subject within the frame, even with explicit pixel coordinates, "X inches from edge" margins, "wide establishing shot" framing, "zoom out the camera by 30%", or "stand 18 feet from camera". All produce visually-identical compositions.

**S73 evidence (Beat It Hubx debug — ~9 NBP iterations):**
- v3: composition lock "preserve input's distance/framing exactly" → no change
- v4: "12 feet from camera, headroom + foot-room ratios" → minor improvement, still ~75% body height
- v5: "wide establishing shot, body ≤40% of vertical frame" → ~60% body
- v6: "feet ≥1 inch from bottom edge" → got the foot clearance but still ~70% body
- v7: "feet 1.5", head 2", 6 ft tall person" → BACKFIRED (the 6ft anchor pushed NBP to render the figure LARGER, not smaller)
- v8/v9: "shift subject 0.5 inches further into scene" + "zoom out camera 30%" → no visible change at all
- v10 (AIMLAPI `google/nano-banana-pro-edit`): finally produced visibly smaller subject — but output was landscape 1376×768, not the requested 1:1. So different model, different behavior — but aspect inconsistent.
- Final fix: manual Photoshop (Select Subject → Free Transform → scale to 70% → Content-Aware Fill the old position).

**Why this happens (hypothesis):** Gemini 3 Pro image edits operate on a learned compositional prior. "Person standing on a boardwalk" maps to a canonical portrait/medium-shot framing regardless of pixel-level instructions. The model is optimized for object/wardrobe/scene swaps within preserved composition — not for compositional repositioning.

**How to apply:**
- For preview-asset NBP regen: include the composition lock from `Memory/feedback_nbp_hybrid_default.md` to PREVENT drift in the first place — that's prevention. If the first NBP output is wrong on subject size/position, do NOT iterate the NBP prompt; jump straight to either:
  1. Manual Photoshop (most reliable) — see `docs/V2_template_creation_runbook.md` Pattern B notes.
  2. AIMLAPI `google/nano-banana-pro-edit` — different model, may respect compositional edits — but you'll need to handle aspect-ratio inconsistency in post.
- Do NOT spend Kling budget testing whether "this NBP iteration is finally close enough" — Kling's motion playback amplifies any composition mismatch (subject too close → head clips, duplicates appear).

**Cost reminder:** each NBP iteration is ~$0.04 (Google AI Studio paid tier), each AIMLAPI nano-banana-pro-edit call was ~$0.19. Manual Photoshop is free + faster + reliable.

See related: [[nbp-hybrid-default]], [[regen-vs-preserve-prompts]], [[localized-edits-cant-holistic-regen]].
