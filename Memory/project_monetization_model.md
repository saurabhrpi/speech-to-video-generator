---
name: Monetization Model
description: Credit-packs only (no subscriptions); anon 10-credit free tier → paywall → paid; sign-in bundled with Apple IAP, never standalone
type: project
---

Monetization model for the shipping mobile app (V1 state, Session 52):

- **Anon users:** 10 free credits granted on first API call = exactly 1 free generation. One-time, not refilling.
- **After free tier:** User hits the **paywall** — never a standalone "please sign in" wall.
- **Sign-in:** Happens *as part of Apple IAP purchase* (anon → Apple account linking at checkout, preserves Firebase UID).
- **Paid:** Signed-in users have NO unlimited free gens. Same credit gate as anon.
- **Product shape: credit packs only (no subscriptions).** Three one-time consumable IAPs (already in ASC):
  - `pro_pack_50` — $4.99 / 50 credits = **5 gens**
  - `pro_pack_120` — $9.99 / 120 credits = **12 gens** (BEST_VALUE)
  - `pro_pack_250` — $19.99 / 250 credits = **25 gens**
- **Per-gen cost: 10 credits = $1.00 retail.** V1 is single-model + single-duration (Hailuo 10s only); future variants slot back into `CREDIT_COSTS` if needed.

**Why credit packs, not subscriptions:** ~$0.50 COGS/gen makes unlimited subs a bankruptcy risk; capped subs feel punitive; "pay per video" matches the impulse use case (one weird thought = one purchase occasion); no churn engineering, cleanest margin math. Subscription revisited at month 3-6 if retention data justifies.

**Why anon-first:** Validated by Sid (friend with successful iOS app) — "don't force login, allow anon, use Firebase." Login walls kill conversion but the app still needs revenue. Paywall with sign-in bundled into the purchase flow is the right gate.

**Margin math (V1, post Session 52 simplification):**
- $0.50 COGS (Hailuo 10s direct via MiniMax) per gen
- Apple Small Business Program (15% cut): user MUST enroll at developer.apple.com → Account → Agreements → Paid Apps. Without enrollment, Apple takes 30%, halving the numbers below.
- After Apple 15%: $0.85 net per $1.00 retail (small pack), $0.68 net (top pack with bulk discount)
- Gross margin: **$0.35/gen at $4.99 pack, $0.18/gen at $19.99 pack** (top pack tighter due to bulk discount; accepted for V1).

**How to apply:**
- Do NOT design features that assume "signed-in = free unlimited." Every gen costs credits, regardless of auth state.
- Future gating is **entitlement-based via credit balance**, not identity-based.
- When the paywall opens, sign-in prompt must be part of the purchase flow, not a separate step that blocks feature use.
- Anon Firebase UID → linked to Apple credential on purchase so gallery / credit balance persists.
- Do NOT propose subscription products without explicitly revisiting this decision.
- Future pack repricing is plausible post-launch — IAPs in ASC are named `pro_pack_50/120/250` so credit AMOUNTS can be tweaked in code without renaming SKUs.
