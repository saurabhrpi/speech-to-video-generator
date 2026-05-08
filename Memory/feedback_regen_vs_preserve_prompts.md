---
name: Regen-framed prompts vs preserve-framed prompts produce different model behavior
description: Image-edit models behave fundamentally differently on "preserve everything except X" prompts (localized edit, paste-in feel) vs "regenerate a coherent photograph combining A and B" prompts (holistic regeneration, integrated output). Same model, same endpoint, same inputs — different output behavior. Always draft both framings up front.
type: feedback
---

Image-edit endpoints (Nano Banana Pro Edit, instruction-following inpaint / edit models) accept arbitrary natural-language prompts. The *framing* of the prompt determines what the model attempts, which in turn determines whether output is locally faithful but globally unintegrated, OR globally integrated but with looser preservation of specific input elements.

**Two distinct prompt framings:**

- **Preserve-framed (localized):** lead with what to preserve, narrowly specify what to change.
  - Example: *"Replace the person in the first image with the person from the second image. Keep the original pose, clothing, background, lighting, and overall composition exactly as in the first image. Only change the face to match the second image's person."*
  - Model behavior: localized edit. The face region is changed; everything else is preserved at the pixel level. Lighting on the new face is locally consistent with what was there before — but globally, the new face often looks pasted in, because the model didn't re-render lighting / shadows / integration with awareness of the broader scene.

- **Regen-framed (holistic):** lead with the operation as a coherent regeneration, give the model latitude.
  - Example: *"Holistic character regeneration. Generate a single coherent photograph by combining elements from the two reference images. From image-1 take pose / scene / lighting / dimensions. From image-2 take identity / face / clothing / accessories. Imagine naturally any body parts not visible in image-2. DO NOT preserve image-1's character or do a localized face swap. Regenerate the entire character holistically so lighting, skin tone, clothing, and pose all look natural and integrated."*
  - Model behavior: holistic regeneration. The entire character region is re-rendered with awareness of the scene. Lighting integrates naturally; specific input elements (e.g. exact pixel-level fidelity to image-1's clothing) drift, but the result feels like one coherent photograph.

**Same model, same endpoint, same inputs — different framings produce dramatically different results.** Don't conflate "this model can't do X" with "I haven't asked this model to do X correctly yet."

**Why:** S58 — Outcome-1 pipeline. v1-v3 used preserve-framing on Nano Banana Pro Edit ("face swap, keep everything else"). Output had clean identity + clean preservation + paste-in face lighting. After three iterations failed to fix the lighting, I declared a "model-class ceiling, localized-edit models can't do holistic integration, switch model class." Wrong. v4 used regen-framing on the same Nano Banana endpoint ("regenerate a coherent photograph combining identity-from-image-2 with pose-and-scene-from-image-1"). Result: clean identity, clean scene, naturally integrated lighting. User verdict "Wow, this is gold." The model didn't change. The framing did.

**How to apply:**
1. **Draft both framings before running anything.** When a pipeline step is "modify image X using image Y as a reference," write two candidate prompts: one preserve-framed, one regen-framed. Run both against the same inputs (~$0.04-0.08 total).
2. **Choose framing based on what your downstream pipeline needs.** If you need pixel-exact preservation of specific elements (logos, exact text, exact face landmarks), preserve-framing is right despite the integration cost. If you need natural integration (lighting, character coherence in a scene), regen-framing is right despite the preservation drift.
3. **When a prompt produces paste-in / unintegrated output, swap to the OTHER framing before iterating the current one.** Don't tune-by-iteration on the wrong framing.
4. **Cross-reference:** `feedback_localized_edits_cant_holistic_regen.md` (the broader rule this is a special case of); `feedback_save_memory_only_after_verification.md` (don't save a "model can't" memory before trying the alternate framing).
