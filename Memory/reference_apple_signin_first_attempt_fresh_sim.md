---
name: Apple Sign In first attempt fails on fresh sim
description: After erasing a sim and signing into iCloud, the first ASAuthorizationAppleIDProvider call usually returns "authorization attempt failed for an unknown reason"; second attempt succeeds
type: reference
---

When a freshly-erased iOS Simulator has just signed into iCloud (via Settings → Sign in to your iPhone), the **first** Apple Sign In attempt the app makes typically fails with:

> "The authorization attempt failed for an unknown reason"

This surfaces in our Paywall as a red banner because `Paywall.handlePurchase` catches the error and sets `purchaseError`. The second tap of Buy works — iCloud has finished provisioning by then.

**Don't chase this as an app bug.** Confirm by retrying. Code path is fine. Optional UX polish: detect this specific error and prompt "tap again" instead of showing the raw message.

After the second successful sign-in, expect the iOS sandbox account selector to appear (separate dialog, asks to "choose the only account listed" + password). This is iOS associating a sandbox tester with the iCloud account for IAP flows. Then the actual purchase sheet (real App Store sandbox or RC Test Store, depending on `__DEV__`) appears.
