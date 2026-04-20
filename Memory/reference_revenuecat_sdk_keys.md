---
name: RevenueCat dual SDK keys
description: RC has two distinct SDK public keys per iOS project — appl_ for App Store, test_ for Test Store. Wrong key = offerings fetch errors on simulator. Switch via __DEV__.
type: reference
---

RevenueCat projects expose **two separate iOS SDK public keys**, both accessible in Project settings → API keys:

- **App Store SDK key** (prefix `appl_`): Used when the SDK should resolve against real App Store Connect products via StoreKit. This is the production/TestFlight key.
- **Test Store SDK key** (prefix `test_`): Used when the SDK should resolve against RC's Test Store products (no ASC setup required). This is the dev/simulator key.

**Critical gotcha:** `test_` prefix is ALSO used for v2 REST API secret test keys. To identify the Test Store SDK key, check the label in the dashboard — it should say "Test Store" or sit under the "SDK API Keys" / "Apps & providers" section, NOT under "REST API Keys".

**Failure mode:** configuring the SDK with the App Store key (`appl_`) in a build that has no real ASC products attached to the offering triggers `[RevenueCat] Error fetching offerings - OfferingsManager error 1` on boot. On Expo/RN dev builds this surfaces as a red LogBox error banner. This is not harmless — it means no offering can be fetched at all, so paywall UI that reads from `Purchases.getOfferings()` will have no data.

**Fix pattern (proven in Session 39):**

```ts
// mobile/lib/constants.ts
export const REVENUECAT_IOS_APP_STORE_KEY = 'appl_...';
export const REVENUECAT_TEST_STORE_KEY = 'test_...';

// mobile/lib/purchases.ts
const apiKey = __DEV__ ? REVENUECAT_TEST_STORE_KEY : REVENUECAT_IOS_APP_STORE_KEY;
Purchases.configure({ apiKey });
```

`__DEV__` is `true` for Metro dev builds, `false` for production bundles (TestFlight, App Store). EAS sets this correctly — no manual intervention.

**Test Store feature scope:**
- Simulator purchases work end-to-end — no ASC, no sandbox tester, no StoreKit config file.
- Minimum RC iOS SDK version: 5.43.0 (we are on 10.0.1).
- Test purchases flow through CustomerInfo like real ones — entitlements activate, webhooks fire.
- Switch to `appl_` key before uploading to TestFlight — Test Store products don't exist in Apple's catalog.

**How to apply:**
- When setting up RC for a new Expo project, grab BOTH keys during onboarding, not just the App Store one. Otherwise simulator testing is blocked.
- Don't hardcode a single key — use the `__DEV__` switch so the prod path is safe by default.
- If a future RC error says "Error fetching offerings" on sim, first check whether you're using the Test Store key in dev. That's the #1 cause.
