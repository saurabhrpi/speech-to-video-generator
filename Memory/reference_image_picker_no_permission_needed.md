---
name: reference_image_picker_no_permission_needed
description: expo-image-picker launchImageLibraryAsync needs NO photo-library permission on iOS — don't gate it with requestMediaLibraryPermissionsAsync
metadata:
  type: reference
---

`ImagePicker.launchImageLibraryAsync()` requires **no** photo-library permission on iOS. Verified in expo-image-picker v17 native source (`node_modules/expo-image-picker/ios/ImagePickerModule.swift`): the photo-library launch path NEVER checks `PHPhotoLibrary` authorization — only `launchCameraAsync` guards on a permission. With `allowsEditing: true` it uses the legacy `UIImagePickerController` (which has never required photo-library auth since iOS 11); with `allowsEditing: false` it uses `PHPickerViewController` (out-of-process, also permission-free). The picked image comes back in-memory; the only permission-dependent read is a best-effort `PHAsset` filename that "in the worst case will be null" (`MediaHandler.swift`), which most code doesn't use (we use `asset.uri`).

**So calling `requestMediaLibraryPermissionsAsync()` before `launchImageLibraryAsync()` is a SELF-IMPOSED gate** — and a bug magnet: if that permission is pre-set to `denied` (e.g. the user denied an earlier TestFlight build), the gate blocks the user even though the picker itself would have opened fine. That was the root cause of AIV-96 (dad's fresh-install "Pick a photo" dead-ended at an in-app Alert). Fix = delete the gate, call the picker directly. Strictly better in every state (granted/undetermined/denied/limited), and removes a redundant first-use prompt.

**Only request media-library permission if you genuinely need direct library access** (reading PHAsset metadata, saving — `expo-media-library` with `NSPhotoLibraryAddUsageDescription`, the separate save-to-camera-roll path). Picking one photo is not that case.

Verification used [[reference_simctl_privacy_tcc]] to force denied/undetermined/granted on the sim — all three opened the picker. See also [[feedback_absolute_overlay_button_intercept]].
