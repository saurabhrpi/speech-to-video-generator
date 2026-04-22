---
name: RC Test Store REST API ingestion is slow
description: RevenueCat Test Store transactions take >7s to appear in the public REST subscriber payload; mobile retry windows must accommodate this, and restorePurchases() is unsupported in Test Store
type: reference
---

In dev (`__DEV__`) the mobile app initializes RC with the Test Store SDK key (`test_...`), so `Purchases.purchasePackage` fires a synthetic test purchase. Two quirks to know:

1. **Test transactions DO eventually appear in `/v1/subscribers/{uid}` non_subscriptions**, but ingestion can take >7s. Our mobile retry window for `/api/credits/grant` was 1+2+4=7s and exhausted before the receipt landed. The user had to manually tap Restore (~30+s later) to grant succeed. Fix path: lengthen the retry window in `mobile/lib/purchases.ts:grantCreditsForTransaction` for dev — e.g. `[2, 4, 8, 16]` = 30s — or auto-fall-back to a Restore loop after the first round of 404s.

2. **`Purchases.restorePurchases()` is a no-op in Test Store** — RC logs `"Restoring purchases not available in Test Store. Returning current CustomerInfo."` It returns the cached `CustomerInfo`, but `nonSubscriptionTransactions` is still populated from the original purchase, so iterating and re-calling `grantCreditsForTransaction` works (the receipt has been ingested by RC's REST by the time the user taps Restore). Don't expect Restore to re-fetch from the store.

3. **Server matches via `entry.id` (RC's internal id), not `store_transaction_identifier`.** The matcher in `api/credits.py:_verify_purchase` falls through to `rc_id == transaction_id` for Test Store txIds (which look like `test_177682...`). The Firestore `applied_transactions` array stored the RC internal id (`o1_uxgPGLC8wUllGAeOF2KMKg`), not the store-transaction-id we sent. This is by design — both branches of the OR are intentional.

**Production note:** With the real `appl_` SDK key against App Store sandbox/production, ingestion is faster (typically <3s). The 7s mobile window may be sufficient there, but worth lengthening for safety.
