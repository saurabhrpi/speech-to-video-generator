---
name: supportsTablet false does not block iPad review
description: Setting Expo's `supportsTablet: false` does NOT prevent Apple reviewers from testing on iPad. iPhone-only apps still install in iPad scaled-compat mode and Apple reviews on whatever device they pick.
type: reference
---

When `supportsTablet: false` is set in Expo's `app.json`, the iOS build gets `UIDeviceFamily = [1]` (iPhone-only). Despite the name, this does NOT prevent iPad install or iPad review — it only:

- Removes the "Universal" badge from the App Store listing.
- Skips the 13-inch iPad screenshot requirement at submission (the S52 reason for setting it false).
- Makes iOS run the app in iPhone-scaled compatibility mode on iPad.

Since iOS 13+, Apple deliberately removed the "iPhone-only refuses to install on iPad" behavior. **There is no app.json/Info.plist flag that hides the app from iPads or prevents Apple reviewers from picking an iPad.**

S53 first rejection cited 2.1(b) on iPad Air (Build #12). We assumed `supportsTablet: false` would route reviewers back to iPhone. **It does not.** S54 second rejection (Build #13) was again on iPad Air 11-inch (M3), iPadOS 26.4.1.

**Levers that actually work (or sort of):**
1. **App Review Information notes in ASC** — add "App designed for iPhone; iPad runs in scaled compat mode; please test on iPhone if possible." Reviewers may or may not honor it.
2. **Fix the iPad-scaled-mode bugs.** Real ones exist:
   - Modal-on-modal stacking is worse in compat mode (see `reference_ios_modal_on_modal.md`).
   - Paywall + RC offerings sometimes render off-screen or unresponsive in scaled mode.
3. **Test the iPad scaled mode locally** before submission — boot iPad simulator, run app, verify Paywall + IAP + key flows.

**Don't trust `supportsTablet: false` to exclude iPad from review.** Test on iPad simulator regardless.
