---
name: Expo prebuild iOS-only flag
description: npx expo prebuild fails when @react-native-firebase is installed without google-services.json configured. Use --platform ios to skip Android.
type: reference
---

`npx expo prebuild` (no flags) runs config plugins for BOTH iOS and Android. In an iOS-only project that uses `@react-native-firebase/app` (or similar Firebase plugins), the Android config plugin hard-fails with:

```
[android.dangerous]: withAndroidDangerousBaseMod: Path to google-services.json is not defined.
Please specify the 'expo.android.googleServicesFile' field in app.json.
```

Even if you never intend to build for Android, prebuild errors out and the iOS native project is never regenerated.

**Fix:**
```
npx expo prebuild --platform ios
```

Skips Android config plugins entirely, regenerates only `ios/`. This is the correct invocation for any session where only iOS is being built.

**How to apply:**
- Any time a new native module is added to the Expo project, the next prebuild should use `--platform ios` unless Android is also being shipped.
- The iOS-side warnings you'll still see are harmless and expected: `REVERSED_CLIENT_ID not found in GoogleService-Info.plist` (only matters if Google Sign-In is used — this app uses Apple Sign In only) and `Skipping iOS openURL fix because no 'openURL' method was found` (expected for the RNFB Auth plugin when no custom URL scheme handling exists).
- If Android is ever added: supply `google-services.json` and set `expo.android.googleServicesFile` in `app.json`.
