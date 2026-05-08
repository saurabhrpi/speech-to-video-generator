---
name: Localized-edit models can do holistic integration — but only with regen-framed prompts
description: Image-edit models like Nano Banana Pro Edit can produce either localized-edit output (paste-in feel, no scene integration) OR holistic-regen output (naturally integrated lighting/character) depending on how the TASK is framed in the prompt. "Preserve everything except X" gives localized output. "Regenerate the entire scene combining elements A and B" gives integrated output. Try BOTH framings before declaring a model-class ceiling.
type: feedback
---

When evaluating an image-edit model for a multi-step pipeline, the *prompt framing* — not just the model class — determines whether you get localized or holistic output. The same Nano Banana Pro Edit endpoint produces dramatically different behavior depending on which framing you use:

- **Localized framing:** *"Preserve everything from image-1 except X. Change only X to match image-2."* Result: a localized edit. The edited region is faithful to the instruction, but its lighting / integration with the rest of the canvas tends to be unintegrated — paste-in feel.
- **Regen framing:** *"Regenerate a coherent photograph by combining: pose / scene / lighting from image-1; identity / clothing / accessories from image-2; naturally imagine body parts not visible in image-2. DO NOT preserve image-1's identity. DO NOT do a localized swap."* Result: holistic regeneration. Lighting integrates, character reads as one coherent figure in the scene.

**The two framings target different operations on the same endpoint.** Prompt-iterating the localized version (v1 → v2 → v3) won't fix the paste-in feel — that's a fundamental property of what you asked the model to do. Switching to the regen framing changes what the model attempts.

**Why:** S58 — built a Kling 2.6 Motion Control + Nano Banana Pro Edit pipeline for Outcome 1 (user in template's scene). Iterated the localized framing three times (v1 → v2 → v3), progressively fixing sunglasses + accessories + skin-tone rules. v3 was technically correct (face matched user, accessories rules respected, all preservation rules followed) but the final video still felt paste-in: face lighting didn't match scene lighting. **First conclusion (saved as this memory's earlier version):** "model-class ceiling, localized-edit models can't do integration, switch model class." That was wrong. After a `Match Video` digression, the user proposed a v4 prompt that REFRAMED the task as holistic regen ("regenerate the character combining identity from image-2 with pose/scene/lighting from image-1"). Same Nano Banana endpoint. Result: clean Outcome 1, naturally integrated lighting, user verdict "Wow, this is gold." The model-class ceiling I declared at v3 was an artifact of the v1-v3 framing. Recovering this finding cost ~$0.04 + 8 trial Kling credits to test the v4 reframing.

**How to apply:**
1. When using an image-edit model for a multi-step pipeline, draft TWO prompts up front: one localized-framing ("preserve, edit only X"), one regen-framing ("regenerate combining A and B"). Test both with the same inputs.
2. If localized framing produces paste-in / unintegrated output, do NOT keep iterating the same framing. The ceiling is the *framing*, not the model. Switch to regen framing first; only then consider switching model classes.
3. The "two iterations max" rule still holds within a single framing: don't iterate the same conceptual prompt more than twice. But "two iterations of localized + two iterations of regen" is the right budget — four prompts total max — before declaring a true model-class ceiling.
4. Cross-reference: `feedback_regen_vs_preserve_prompts.md` for the prompt-framing distinction in detail; `feedback_provider_mode_names_neq_outcomes.md` (mode-vs-outcome misreads); `reference_motion_transfer_two_outcomes.md` (two-outcome taxonomy).
