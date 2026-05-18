---
name: Monetization Model
description: Credit-packs only (no subscriptions); anon 10-credit free tier → paywall → paid; sign-in bundled with Apple IAP, never standalone
type: project
---

Monetization model — current state at V2.0.0 launch (S67 update):

- **Anon users:** 25 free credits granted on first API call (was 10 at V1) = exactly 1 free template generation (25-cr cost). One-time, not refilling.
- **After free tier:** User hits the **paywall** — never a standalone "please sign in" wall.
- **Sign-in:** Happens *as part of Apple IAP purchase* (anon → Apple account linking at checkout, preserves Firebase UID).
- **Paid:** Signed-in users have NO unlimited free gens. Same credit gate as anon.
- **Product shape: credit packs only (no subscriptions).** Three one-time consumable IAPs (SKUs unchanged from V1; prices + credit counts updated for V2):
  - `pro_pack_50` — **$5.99** / 50 credits
  - `pro_pack_120` — **$15.99** / **150 credits** (SKU name retains "120" — ASC SKUs are immutable; display name in ASC is "150 Credits")
  - `pro_pack_250` — **$24.99** / 250 credits (**BEST_VALUE** — $0.0999/cr beats mid pack's $0.1066/cr)
- **Per-gen cost: 10 credits for V1 S2V (Hailuo 10s), 25 credits for V2 motion-transfer templates.** Per-template `credit_cost` schema field supports variance; all V2.0.0 launch templates are 25 (matches anon starter so anons get exactly 1 free gen).

**Why credit packs, not subscriptions:** ~$0.50 COGS/gen for V1 S2V, ~$1.32 COGS/gen for V2 templates — both make unlimited subs a bankruptcy risk; capped subs feel punitive; "pay per video" matches the impulse use case; no churn engineering, cleanest margin math. Subscription revisited at month 3-6 if retention data justifies.

**Why anon-first:** Validated by Sid (friend with successful iOS app) — "don't force login, allow anon, use Firebase." Login walls kill conversion but the app still needs revenue. Paywall with sign-in bundled into the purchase flow is the right gate.

**V2.0.0 margin math (templates, post-Apple 15% Small Business):**
- COGS: ~$1.32/template gen (NBP regen $0.05 + Kling Motion Control)
- Per-pack margin: Small +$2.45 (41%), Mid +$5.67 (35%), Top +$8.04 (32%) — healthy across the board
- Per-credit retail: $0.1198 / $0.1066 / $0.0999 — top pack has lowest per-credit (badge target)
- Per-template retail (25 cr): $2.99 / $2.66 / $2.50 depending on pack. Margin per gen: $1.67 / $1.34 / $1.18.

**How to apply:**
- Do NOT design features that assume "signed-in = free unlimited." Every gen costs credits, regardless of auth state.
- Future gating is **entitlement-based via credit balance**, not identity-based.
- When the paywall opens, sign-in prompt must be part of the purchase flow, not a separate step that blocks feature use.
- Anon Firebase UID → linked to Apple credential on purchase so gallery / credit balance persists.
- Do NOT propose subscription products without explicitly revisiting this decision.
- Future pack repricing is plausible post-launch — IAPs in ASC are named `pro_pack_50/120/250` so credit AMOUNTS can be tweaked in code without renaming SKUs.
