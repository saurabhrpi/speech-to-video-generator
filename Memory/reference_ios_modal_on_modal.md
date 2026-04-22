---
name: iOS rejects stacking RN Modal over a modal-presented route
description: RN <Modal> silently fails when opened over an expo-router screen with presentation:'modal'; InteractionManager doesn't wait for iOS dismiss; use setTimeout(400)
type: reference
---

iOS UIKit rejects presenting a second view controller on one already presenting. With expo-router declaring a screen as `presentation: 'modal'` (e.g. Settings in `_layout.tsx`) and an RN `<Modal>` at root level (e.g. Paywall), tapping a button inside the modal route to open the Paywall fails silently.

**Log signature:**
```
Attempt to present <RCTFabricModalHostViewController: ...> on <UIViewController: ...>
which is already presenting <RNSScreen: ...>.
```

**Symptoms:** button press registers (haptic + press animation fire) but no modal appears. Zustand's `paywallOpen` flips to true but nothing renders. Lingering `visible={true}` leaves an invisible touch layer → app looks hung.

**`InteractionManager.runAfterInteractions` does NOT wait** for iOS native modal dismiss animations — it only tracks JS-scheduled interactions (gestures, reanimated). Using it as a "wait for dismiss" primitive fails identically to no wait at all.

**Working fix (Session 49, `mobile/app/settings.tsx`):** dismiss the modal route first, wait past the ~350ms iOS dismiss animation, then open the second modal:
```tsx
router.back();
setTimeout(() => openPaywall(), 400);
```

**Better long-term options if the timing hack becomes flaky:**
- Refactor the second modal off `<Modal>`: either use `transparent={true}` on the Modal (iOS allows transparent modals to stack via UIModalPresentationOverFullScreen), or render as a root-level conditional full-screen `<View>`.
- Listen to navigation `state` events at the root to queue the second modal's opening after the first's dismiss is confirmed.
