---
name: Monetization Model
description: Business model = anon free tier → paywall → paid; sign-in is bundled with Apple IAP purchase, never a standalone gate
type: project
---

Monetization model for the app:

- **Anon users:** Small free tier (currently `UNAUTH_GEN_LIMIT=1`).
- **After limit:** User hits a **paywall** — never a standalone "please sign in" wall.
- **Sign-in:** Happens *as part of Apple IAP purchase* (anon → Apple account linking at checkout, preserves Firebase UID).
- **Paid:** Signed-in users are NOT given unlimited free gens. Sign-in MUST lead to payment.

**Why:** Validated by Sid (friend with successful iOS app) — "don't force login, allow anon, use Firebase." Interpreted with the user's monetization intent: login walls kill conversion, but the app still needs revenue. Paywall (with sign-in bundled into purchase) is the right gate.

**How to apply:**
- Do NOT design features that assume "signed-in = free unlimited." Current server.py treats signed-in as unlimited — that's a **placeholder** pending IAP integration.
- Future gating should be **entitlement-based** (has active subscription / credits), not identity-based. Both anon and signed-in users hit the paywall when they run out of free gens / entitlement.
- When the paywall is built, sign-in prompt must be part of the purchase flow, not a separate step that blocks feature use.
- Anon Firebase UID → linked to Apple credential on purchase so gallery / usage counts persist.
