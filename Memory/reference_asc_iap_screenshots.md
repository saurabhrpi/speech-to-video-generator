---
name: ASC IAP review screenshots from simctl, not framed mockups
description: App Store Connect IAP review screenshots must match an exact iPhone display resolution. Cleanshot/device-frame mockups get rejected because the bezel pixels throw the dimensions off. Always use raw simctl screenshot.
type: reference
---

S51: Uploading the Paywall framed-mockup screenshot (658×1384, with simulated device bezels) to ASC IAP review screenshot field → rejected with "The dimensions of one or more screenshots are wrong." Apple's docs link points to App Store screenshot specs, but IAP review uses the same dimension validator.

**The cause:** Apple validates total image dimensions, not the inner rendered content. Device-frame mockups add bezel pixels around the actual screen content, breaking the spec.

**The fix:** Use `xcrun simctl io booted screenshot <path>`. Captures at the simulator's native pixel resolution, which IS one of Apple's accepted iPhone sizes (since the simulator emulates a real iPhone). Example output sizes:
- iPhone 17 Pro Max: 1320×2868 (6.9", current required size)
- iPhone Plus: 1290×2796 (6.7")
- iPhone XS Max: 1242×2688 (6.5")

Any of those pass.

**Marketing screenshots ≠ IAP review screenshots:**
- App Store **marketing** screenshots (public listing): need a set per display class (6.9" required, 6.5" optional fallback).
- IAP **review** screenshots (what App Review sees): just **one** per IAP, must match any one accepted iPhone size. Most devs reuse the same paywall capture across all consumable variants in the same offering.

**Per-pack capture trick:** before each simctl screenshot, tap the relevant pack on the sim so the white border + CTA text reflect that IAP. Three captures, one per IAP, takes <2 minutes.
