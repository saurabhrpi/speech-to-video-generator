# Product Requirements

Hard constraints that shape every product/architecture/model decision. Read at the start of every session. Add new constraints here as they get locked in; don't delete unless explicitly retired.

---

## Motion-transfer model: single-image character input

Any motion-transfer model under consideration for the template-grid product (dance / motion-transfer rows) MUST accept a **single user photo** as the character input. Models that require multiple character images (front + side, multiple angles, reference sets, etc.) are disqualified.

**Why:** The product's core friction promise is one selfie → one video. Asking a casual user to upload 3-5 angled photos breaks the impulse-to-output flow that defines our wedge vs. the bigger AI-video apps. Mobile users will abandon a multi-photo upload step. Non-negotiable for V1 and V2.

**How to apply:**
- When evaluating any new motion-transfer provider (Higgsfield, Pollo Mimic, Pixverse, Wan 2.2 Animate, Bytedance Imitator, Runway Act-2, future entrants), confirm single-image character support BEFORE deeper integration analysis. If the docs/API require >1 character image, drop it from the shortlist immediately — don't waste time on quality/pricing comparisons.
- Driving-video / motion-reference inputs are a separate question — those can be hosted by us (preprocessed scenes, template registry) and don't touch this constraint. The constraint is purely about what the END USER must upload.
- Re-verify on each new provider's docs; some models offer both single-image and multi-image modes — single-image must be a first-class supported mode, not a degraded fallback.
