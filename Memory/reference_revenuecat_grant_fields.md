---
name: RC purchase grant fields
description: After Purchases.purchasePackage in react-native-purchases, which fields to send to a server that verifies via the RC REST API
type: reference
---

After `const res = await Purchases.purchasePackage(pkg)` (react-native-purchases v10+):

- `res.transaction.transactionIdentifier` — the store transaction id. RC's REST `/v1/subscribers/{uid}` surfaces this under `subscriber.non_subscriptions[product_id][*].store_transaction_identifier`. Send this as `transaction_id` to your server.
- `pkg.product.identifier` — the store (App Store / Test Store) product id. This is the key under `subscriber.non_subscriptions` in the RC REST payload. Send this as `product_id` to your server. **Do not** use `pkg.identifier` (the RC-dashboard package id) for grants — it works only if you happen to set it equal to the product id in the dashboard, and silently breaks if they diverge.

For **Restore**: `customerInfo.nonSubscriptionTransactions: PurchasesStoreTransaction[]`. Each entry has `transactionIdentifier` + `productIdentifier` (the store product id). Filter by your known SKU list and re-grant per entry — server-side grants must be idempotent by `transaction_id`.

For **404 on grant**: RC's backend lags behind the store by seconds. Retry with exponential backoff (1s/2s/4s works) on `404 purchase_not_found_yet` before surfacing an error. Other 4xx/5xx should fail fast.

`MakePurchaseResult` type ships from `@revenuecat/purchases-typescript-internal` — check `node_modules/@revenuecat/purchases-typescript-internal/dist/callbackTypes.d.ts` and `customerInfo.d.ts` to confirm exact fields when the SDK is upgraded.
