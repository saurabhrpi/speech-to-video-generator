---
name: Paid Apps Agreement must be Active before App Store submission with IAPs
description: Pending agreement causes RC to return empty products, which Apple cites as 2.1(b) "buy button unresponsive" — verify all three Business rows Active before clicking Add for Review
type: reference
---

If an iOS app has IAPs and the **Paid Apps Agreement** is in **"Pending User Info"** status (not "Active"), App Store Connect refuses to expose IAP products via StoreKit. RevenueCat's `Purchases.getOfferings()` returns the in-app red error: *"None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect."* Tapping any package button does nothing because there are no products to purchase.

**Apple's review interpretation:** the silent failure is cited as **Guideline 2.1(b) (App Completeness — buy button unresponsive)**. Apple's review note typically hints at the cause: *"Confirm you have a Paid Apps Agreement in effect."* Verified S53 — we got rejected on exactly this.

**How to verify before clicking Add for Review:** ASC → Business → confirm all three rows show **Active**:
1. Paid Apps Agreement
2. Bank Account
3. Tax Form (W-9 for US individual; W-8BEN for non-US individual; W-8BEN-E for non-US entity)

**Timing reality:**
- W-9 / W-8BEN: instant submission, instant Active
- Bank Account: 1-3 business days for ACH micro-deposit verification (sometimes hours via instant verification)
- Paid Apps Agreement auto-flips to Active once both Bank + Tax show Active

**How to apply:** before clicking "Add for Review" on any submission with IAPs, screenshot the Business page showing all three rows Active. Don't trust ASC banners alone — they sometimes show "Pending User Info" even after submission. The `restoreAndGrant`-empty / RC-products-empty / 2.1(b)-rejection chain is the diagnostic signature; if you see RC's "products empty" red box on the Paywall during dev testing, the agreement is the most likely cause, not RC config.
