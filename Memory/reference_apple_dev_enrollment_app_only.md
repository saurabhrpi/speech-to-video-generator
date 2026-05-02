---
name: Apple Developer Program enrollment is App-only on web today
description: Web sign-in at developer.apple.com offers ONLY "install Apple Developer App" — no webcam-based browser flow; non-App users must use the "contact us" link for manual support-driven enrollment
type: reference
---

When a user signs into developer.apple.com (Apple Developer Program enrollment) from a non-iOS device (e.g., Windows, Mac browser without iOS device handy), the page presents **a single primary option**: install the Apple Developer App on iPhone/iPad. Below that, in small print, is a *"if you cannot download the Developer app, please contact us"* escape link. There is **no in-browser webcam-based enrollment flow** for self-service users today (verified S53 via direct user observation, dad in India, Windows browser).

**Implication:** prior assumptions that "web browser with webcam works as a fallback" are wrong as of S53. Apple has consolidated enrollment into the iOS App for self-service, with the support-contact path as the only documented non-App option.

**Realistic enrollment surfaces (in order of friction):**
1. **Apple Developer App on any iOS device with camera** — fastest, fully self-service. Single ID photo, no required selfie for most regions. ~15 min active + 24-48h Apple review.
2. **"Contact us" link from the web sign-in page** → opens Apple Developer Support request. User explains no iOS device, asks for non-App enrollment. Manual / email-based ID verification follows. ~1-3 business days for response, longer total cycle.
3. NOT viable: web browser with webcam capture for self-service enrollment.

**Per-device Apple ID creation cap is independent.** Even with an iOS device, Apple silently caps Apple ID creations per device (~3/year, undocumented lifetime ceiling). Hitting it produces the generic "Your account cannot be created at this time" — same error as IP-rate-limit, with no diagnostic distinction. If a device fails, jump to a different iOS device or the support path rather than retrying.

**How to apply:** when guiding a non-iOS user (Windows desktop user, etc.) through Apple Developer enrollment, recommend: (a) borrow an iOS device for the App flow, OR (b) click the "contact us" small-print link for the support path. Don't suggest "use the web browser flow" — it doesn't exist as a self-service option today.
