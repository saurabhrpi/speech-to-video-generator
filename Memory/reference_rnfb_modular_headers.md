---
name: RNFB non-modular header fix
description: Expo SDK 54 + RN 0.81 + @react-native-firebase/app@24 + useFrameworks:static triggers non-modular header errors in RNFBApp/RNFBAuth — fix with forceStaticLinking in expo-build-properties
type: reference
---

## Symptom

EAS build fails at Xcode stage with `-Wnon-modular-include-in-framework-module` errors like:

```
include of non-modular header inside framework module 'RNFBApp.RCTConvert_FIRApp': '...React-Core/React/RCTConvert.h'
```

Affects `RNFBApp.*` and `RNFBAuth.*` targets importing React-Core headers.

## Root cause

SDK 54 regression — the prebuild Podfile stopped forcing `@react-native-firebase` pods to be static libraries. With `useFrameworks: "static"`, Cocoapods compiles RNFB pods as framework modules, but React-Core isn't built modular, so Clang errors. Refs: [expo/expo#39607](https://github.com/expo/expo/issues/39607), [invertase/react-native-firebase#8657](https://github.com/invertase/react-native-firebase/issues/8657).

## Fix

In `mobile/app.json`, add `forceStaticLinking` to the `expo-build-properties` ios block:

```json
["expo-build-properties", {
  "ios": {
    "useFrameworks": "static",
    "forceStaticLinking": ["RNFBApp", "RNFBAuth"]
  }
}]
```

This makes RNFB pods build as static libs (not framework modules), so the non-modular include rule no longer applies.

## Notes

- `forceStaticLinking` is a real `expo-build-properties` option (verified in `node_modules/expo-build-properties/src/pluginConfig.ts` at v1.0.10).
- Do NOT disable `newArchEnabled` — new arch works fine with the fix.
- Alternate approach is `extraPods` with `modular_headers: true` but didn't match our exact error shape.
- If a new RNFB sub-package is added later (e.g. `@react-native-firebase/firestore`), add its corresponding `RNFB<Name>` to the `forceStaticLinking` array.
