---
name: Apple App Transfer prerequisites (verified S53)
description: Verbatim Apple App Transfer criteria; in particular there is NO 60-day cooldown rule despite my prior assertion of one
type: reference
---

Verified S53 against Apple's docs at https://developer.apple.com/help/app-store-connect/transfer-an-app/app-transfer-criteria.

**Mandatory criteria for App Transfer:**

1. **App release history:** "The app must have at least one version that was released to the App Store." TestFlight-only or rejected-only apps cannot be transferred.
2. **Account status:** both transferor and recipient accounts must NOT be in pending/changing state; both parties must have accepted the latest paid + free agreements.
3. **EU Alternative Terms Addendum:** if transferor accepted it, recipient must accept it before transfer can complete.
4. **No pre-order status** active.
5. **App version status must NOT be:** Processing for Distribution, Waiting for Review, In Review, Accepted, Pending Developer Release, Pending Apple Release.
6. **IAP product status must be one of:** Approved, Ready to Submit, Developer Removed from Sale, Rejected.
7. **No conflicting IAP product IDs** between source app and any app in recipient's account.
8. Various Mac/Apple Arcade/Asset Pack restrictions (rarely relevant to typical iOS apps).

**Important non-finding: NO 60-day cooldown rule.**

I previously asserted that App Transfer had a 60-day cooldown between transfers (or after first release). Apple's current published criteria do NOT mention any such rule. The transfer window opens immediately after first App Store release; subsequent transfers are not gated by a documented cooldown either.

**How to apply:** when discussing transfer timing, gate only on: first App Store release done + app version not in an in-flight review state + IAPs in valid status. Don't add fictitious cooldown waits.
