---
name: RevenueCat serves offerings from disk cache when offline
description: getOfferings() succeeds from disk cache for returning users offline, paywall renders normally; failure moves to purchasePackage/restore handlers
type: reference
---

Confirmed in Session 49, live on dev sim with Mac WiFi off.

`Purchases.getOfferings()` does NOT reject when offline. For a returning user with a cached offering on disk, RC serves cached data and `result.current` populates with real prices.

**Log signature:**
```
[RevenueCat] API request failed ... internet connection appears to be offline.
[RevenueCat] Vending Offerings from disk cache
[RevenueCat] ⚠️ Error fetching offerings. Using disk cache
```

**Observed UI (offline, returning user):**
- Paywall renders normally.
- All 3 pack rows populated with real prices from cache.
- NO `loadError` banner (cache succeeded → no error).
- Pack selection still works (local state).

**Failure surface moves to Buy/Restore handlers:**
- `Purchases.purchasePackage` → rejects with `Error performing request because the internet connection appears to be offline.` The Paywall catches this and renders it in the red `purchaseError` banner inline.
- `Purchases.restorePurchases` → in Test Store, returns cached CustomerInfo silently ("Restoring purchases not available in Test Store"). In App Store, would attempt network + fail.

**Fresh-install offline (no cache on disk) NOT directly verified** — expected behavior per code: `getOfferings()` rejects → `loadError` banner with message, rows dimmed, CTA "Loading…". Real reproduction is narrow (requires erased sim + offline before any paywall open); deprioritized.

**Implication:** offline-aware UX must live on Buy/Restore handlers AND a visible network indicator. Relying on paywall load state alone will miss returning users entirely.
