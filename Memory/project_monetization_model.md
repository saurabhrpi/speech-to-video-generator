---
name: Monetization Model
description: Credit-packs only (no subscriptions); anon free tier → paywall → paid; sign-in bundled with Apple IAP purchase, never a standalone gate
type: project
---

Monetization model for the app:

- **Anon users:** Small free tier (currently `UNAUTH_GEN_LIMIT=1`).
- **After limit:** User hits a **paywall** — never a standalone "please sign in" wall.
- **Sign-in:** Happens *as part of Apple IAP purchase* (anon → Apple account linking at checkout, preserves Firebase UID).
- **Paid:** Signed-in users are NOT given unlimited free gens. Sign-in MUST lead to payment.
- **Product shape: credit packs only (no subscriptions).** One-time consumable IAPs, each pack = N generations. Decided 2026-04-19.
- **Tier shape (2026-04-19): two tiers only — `Free` (1 gen gate) and `Pro` (one paid consumable pack).** Pricing + pack size intentionally deferred — decide later once we have paywall UX working. No "Taster/Creator/Pro" ladder; if conversion on single-Pro-tier is weak we revisit tier count then, not upfront.

**Why:** Validated by Sid (friend with successful iOS app) — "don't force login, allow anon, use Firebase." Login walls kill conversion but app still needs revenue. Paywall with sign-in bundled into purchase is the right gate.

Credit packs over subs because: $7 COGS per gen makes unlimited subscriptions a bankruptcy risk; capped subs feel punitive; "pay per renovation" matches the mental model of the app (one timelapse = one purchase occasion); no churn engineering, cleanest margin math. Subs can be added later if credit packs feel too transactional.

**How to apply:**
- Do NOT design features that assume "signed-in = free unlimited." Current server.py treats signed-in as unlimited — that's a **placeholder** pending IAP integration.
- Future gating is **entitlement-based via credit balance**, not identity-based. Both anon and signed-in users hit the paywall when they run out of free gens / credits.
- When the paywall is built, sign-in prompt must be part of the purchase flow, not a separate step that blocks feature use.
- Anon Firebase UID → linked to Apple credential on purchase so gallery / usage counts persist.
- Do NOT propose subscription products without explicit revisit of this decision.
- Margin math: $7 COGS + 15% Apple Small Business cut means sale price must be $8.82+ per gen just to break even. Per-gen pricing below $10 is unsafe.
