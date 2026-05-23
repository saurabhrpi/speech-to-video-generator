---
name: nbp-hybrid-default
description: S73-locked default NBP prompt approach for template preview regen — hybrid (permissive). Constrain what NOT to do, give NBP a small menu of options, specify register not specifics. Beats both fully-explicit (over-engineered) and fully-implicit (unreliable). Locked to avoid prompt-craft debate per template.
metadata:
  type: feedback
---

**Rule:** When writing the NBP edit prompt for a new template preview chain script (`scripts/test_<slug>_chain.py`), use the **hybrid-permissive** approach. Not fully explicit, not fully implicit.

**The three patterns:**

| Pattern | Example | When to use |
|---|---|---|
| Fully explicit | "olive shirt, stone-grey chino shorts, off-white sneakers, coastal boardwalk with palm trees" | Avoid — over-engineered, requires me to make creative choices the user could make better |
| **Hybrid-permissive (S73 default)** | "shirt in a register that's NOT the input's beige (e.g. mint, peach, or earth-tone — pick one); indoor home scene similar register but distinct composition" | **DEFAULT** |
| Fully implicit | "make it visually distinct from this reference, you decide the specifics" | Avoid — unreliable; may drift far from dance-template register |

**Hybrid template structure:**
- **Subject change:** "DIFFERENT young [woman/man/child] — different facial features and identity. Different [hair color OR style], different [skin tone OR age register]."
- **Wardrobe:** "register that's NOT the input's [original]. E.g. [option 1], [option 2], [option 3] — pick one."
- **Scene:** "similar register to the input but distinct composition. E.g. [option 1], [option 2], or [option 3]."
- **Pose:** preserve the input's dance pose register (don't change).
- **Composition lock (S73 critical):** "Subject must occupy the SAME proportion of the frame as the person in the input image — same head height/position, same body size relative to the frame edges. Do NOT zoom in, do NOT zoom out, do NOT move the subject closer to or further from the camera. Preserve the input's camera-to-subject distance and framing exactly."
- **Constraints:** explicit UI removal, 1:1 aspect, full body head-to-feet, face visible.

**Why composition lock matters (S73 Beat It / Smooth Criminal lesson):**
When the driving video has camera-approach or camera-pullback motion (dancer walks toward/away from camera), Kling applies that motion register to our NBP-rendered subject. If NBP rendered the subject closer than the source's t=0 distance, the subject ends up clipped (head out of frame, body too close); Kling sometimes fallback-hallucinates a duplicate subject to land final poses. If NBP rendered farther than source's t=0, the subject looks too far during the camera-pullback segments. Symmetric bounds — both "don't zoom in" AND "don't zoom out" — are required. The composition-lock constraint forces NBP to match the source frame's camera-subject distance exactly, so Kling's motion playback stays inside the safe rendering envelope throughout.

For static-camera drivers (no approach/pullback — Bombale, Baby Dance), composition lock has no visible effect but costs nothing to include — keep it on by default.

**Why hybrid wins:**
- Empirically (S73): produced clean visually-distinct results on Baby Dance Hubx (mint joggers / chestnut curls / cozy home — all from the menu I provided) and Smooth Criminal Hubx (burgundy ribbed knit / black athletic shorts / loft brick wall — same).
- Fully explicit (Beat It v1 → "fair-to-medium skin, beige linen, park canopy") rendered too close to the original because the explicit specs locked NBP into the source register.
- Fully implicit was never tested, but the risk profile is clear: NBP may pick wildly off-register choices that break the dance-template tone.

**How to apply:**
- Lock the prompt shape per the template structure above; don't re-debate the explicit-vs-implicit-vs-hybrid axis per template.
- Per-template variation lives in the menu options (color suggestions, scene type alternatives), NOT in the prompt structure.
- If a first-pass output comes back too close to the input (S73 Beat It v1 problem), do ONE retry with the chain script's "explicit difference-introduction" mode — but still hybrid (give NBP a menu of options for what to change).

**Don't reopen this debate per template.** If you find yourself debating "should I be more specific about the wardrobe?" — the answer is no, use the hybrid menu pattern from the template above.

See related: [[regen-vs-preserve-prompts]], [[localized-edits-cant-holistic-regen]], [[no-overfit-prompts]].
