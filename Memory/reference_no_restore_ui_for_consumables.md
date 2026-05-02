---
name: No user-facing Restore Purchases UI for consumable-only apps
description: Apple Guideline 3.1.1 forbids Apple-account-based Restore for consumable IAPs; consumable-only apps must omit the UI entirely
type: reference
---

Apple's Guideline 3.1.1 explicitly states **consumable IAPs cannot be restored via the user's Apple Account / password**. For an app whose IAPs are **all consumable** (e.g., one-time credit packs, in-game gems, single-use unlocks), do **not** include a user-facing "Restore Purchases" button anywhere — not in Settings, not on the Paywall, not as a quiet link.

**Why this is a trap:** Most React Native / RevenueCat tutorials and starter templates include a Restore button by default — it's the standard pattern for non-consumable / subscription apps. For consumable-only apps, including it is a guideline violation even if the underlying StoreKit `restorePurchases` call returns nothing useful in practice.

**What Apple does:** rejects under 3.1.1 with text like *"the app includes a feature to restore previously purchased In-App Purchase products by entering the user's Apple Account and password. However, consumable In-App Purchases cannot be restored in this manner. To resolve this issue, please revise your binary to implement your own restore mechanism, if you would like users to be able to restore consumable In-App Purchase products."* Verified S53.

**Fix pattern:** remove the user-facing UI entirely. The underlying RC helper (e.g., `restoreAndGrant` in `lib/purchases.ts`) can stay for internal use — Apple inspects only the binary's UI, not internal helpers. Don't preserve the UI as "disabled" or "for emergencies"; just remove it.

**For edge-case purchase recovery without a Restore button** (e.g., StoreKit returns no transaction id, or server grant fails after a successful purchase): implement RevenueCat's `Purchases.addCustomerInfoUpdateListener` (offline-replay listener) to auto-replay missed transactions in the background. Until that lands, point users to support email for the rare cases. See ToDo #19.

**Update Paywall error messages too:** any error string referencing "tap Restore" needs rewording (we changed both ours to point to support email).
