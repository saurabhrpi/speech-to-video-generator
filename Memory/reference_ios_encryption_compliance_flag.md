---
name: ITSAppUsesNonExemptEncryption auto-clears ASC encryption panel
description: app.json infoPlist has ITSAppUsesNonExemptEncryption=false; ASC's App Encryption Compliance panel auto-clears on every upload, no manual questionnaire
type: reference
---

`mobile/app.json` `ios.infoPlist.ITSAppUsesNonExemptEncryption: false` is set. Effect: ASC's "App Encryption Compliance" panel auto-clears on every TestFlight upload — no manual "Does your app use encryption?" questionnaire to fill out per version.

This declaration covers our case because the app only uses standard HTTPS via system networking — no custom crypto. If we ever ship a feature that uses encryption beyond exempt categories (e.g., custom crypto, non-Apple TLS implementation, encrypted-at-rest user data with our own algorithm), this flag must change to `true` and we'd need to complete the export-compliance questionnaire per version.

The flag survives across `npx expo prebuild` because it's declared in `app.json` (Expo regenerates the iOS project from it). No manual Info.plist editing needed.
