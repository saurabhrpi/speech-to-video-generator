---
name: Apple Guideline 4.8 Sign in with Apple rule
description: Apple Sign In mandatory ONLY if app offers other social logins; Apple-only is compliant; no-auth is compliant
type: reference
---

Apple App Store Guideline 4.8 (Sign in with Apple): an app MUST offer Apple Sign In if and only if it offers any other third-party social login (Google, Facebook, etc.). The rule runs in one direction — social-login → Apple required.

Four patterns:

1. **Apple Sign In only** → compliant (no other providers = no 4.8 trigger)
2. **Apple Sign In + other providers** → compliant
3. **No social logins at all** (email/password only, or no auth) → compliant
4. **Google/Facebook without Apple** → NON-COMPLIANT, guaranteed rejection

Beta App Review enforces this too — it's not only full review. For iOS-only apps, Apple-only is the simplest compliant path since every iOS user already has an Apple ID; zero user lockout, and you can add Google later without re-triggering 4.8 (Apple is already there).

Rejection reason cited is usually "Guideline 4.8 — Design — Sign in with Apple".

Related: Guideline 5.1.1(v) requires in-app account deletion for any app offering Sign in with Apple, and the deletion flow must call Apple's token revocation API server-side. So even though the native iOS sign-in flow doesn't strictly need the .p8 key, you still need it configured in your backend / Firebase for account deletion compliance.
