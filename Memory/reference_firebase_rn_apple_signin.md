---
name: Firebase RN native Apple Sign In gotchas
description: Non-obvious config details for @react-native-firebase/auth + expo-apple-authentication — Services ID workaround, useFrameworks requirement, nonce pattern, anon-to-Apple linking
type: reference
---

Five non-obvious details when wiring Apple Sign In into an Expo RN app via `@react-native-firebase/auth` + `expo-apple-authentication` (native flow, not web OAuth):

1. **Services ID is a required-but-unused field.** Firebase's Apple provider config requires a Services ID value once you toggle Enable, but it's only actually used for web OAuth code flow. Native iOS bypasses it entirely (the flow goes `expo-apple-authentication → identityToken → AppleAuthProvider.credential → signInWithCredential`). **Workaround:** put the iOS bundle ID as the Services ID value — Firebase only validates format (reverse-DNS), not Apple registration. No need to actually create a Services ID in Apple Developer portal.

2. **.p8 key still needed even for native-only flow.** Required for server-side Apple token revocation, which Apple App Store Guideline 5.1.1(v) mandates for in-app account deletion. Without .p8 + Key ID + Team ID configured in Firebase, account deletion will fail review. Create the key under Apple Developer → Keys → "+" with Sign in with Apple capability.

3. **`useFrameworks: "static"` is mandatory for iOS.** `@react-native-firebase/app` requires iOS static frameworks. Add via expo-build-properties plugin in app.json:
   ```json
   ["expo-build-properties", { "ios": { "useFrameworks": "static" } }]
   ```
   Without this, Pods won't link correctly. Run `npx expo prebuild --clean --platform ios` after adding.

4. **Nonce pattern is mandatory, order-sensitive.** Flow: generate raw nonce → SHA-256 hash it → pass the **hashed** nonce to `AppleAuthentication.signInAsync({ nonce: hashedNonce })` → pass the **raw** nonce (plus the identityToken Apple returns) to `auth.AppleAuthProvider.credential(idToken, rawNonce)`. Firebase verifies by hashing the raw nonce server-side and matching the claim in the token. Skipping or swapping raw/hashed causes `auth/invalid-credential`.

5. **`linkWithCredential` preserves anonymous UID.** For anon-first auth patterns: if `auth().currentUser.isAnonymous`, call `currentUser.linkWithCredential(appleCred)` to upgrade — the UID stays the same, so backend data keyed off UID (clips, usage) carries over seamlessly. Catch `auth/credential-already-in-use` (same Apple account already a Firebase user elsewhere) and fall back to `auth().signInWithCredential(appleCred)`, which orphans the anonymous user's data — acceptable if migration isn't required.
