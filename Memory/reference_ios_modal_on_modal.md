---
name: RN Modal stacking with iOS native presentations is fragile — use root-level overlay View
description: RN <Modal> creates a separate iOS window; stacking with expo-router modal routes (rejected presentation) OR native sheets like Apple Sign In (focus-stuck on dismiss) breaks. Refactor off Modal to Animated.View overlay.
type: reference
---

RN's `<Modal>` creates a separate iOS window via `UIModalPresentationFullScreen` (or `OverFullScreen` when `transparent={true}`). It does NOT play well when stacked with other iOS-presented views — both directions of stacking break:

## Scenario A: opening RN Modal over an expo-router modal route

iOS UIKit rejects presenting a second view controller on one already presenting. With expo-router declaring a screen as `presentation: 'modal'` (e.g. Settings) and an RN `<Modal>` at root level (e.g. Paywall), tapping a button inside the modal route to open the Paywall fails silently.

**Log signature:**
```
Attempt to present <RCTFabricModalHostViewController: ...> on <UIViewController: ...>
which is already presenting <RNSScreen: ...>.
```

**Symptoms:** button press registers (haptic + press animation fire) but no modal appears. Zustand's `paywallOpen` flips to true but nothing renders. Lingering `visible={true}` leaves an invisible touch layer → app looks hung.

`InteractionManager.runAfterInteractions` does NOT wait for iOS native modal dismiss animations — it only tracks JS-scheduled interactions (gestures, reanimated). Using it as a "wait for dismiss" primitive fails identically to no wait at all.

## Scenario B: native iOS sheet stacking on top of RN Modal

A native iOS sheet (Apple Sign In via `appleAuth.performRequest`, IAP confirmation, share sheet) presented on top of an RN `<Modal>` dismisses cleanly at the JS layer, but iOS doesn't restore touch focus to the underlying Modal — children become unresponsive.

**Symptoms:** the sheet's cancel handler fires, JS state updates correctly (`purchasing=false`), but tapping anything in the underlying Modal does nothing. macOS sim cursor over the Modal turns into the "two-triangles-pointing-away" drag-handle indicator — iOS still thinks a sheet is presented even though the JS layer believes it's gone. Only force-kill recovers.

`transparent={true}` on the Modal does NOT fix this (S50 confirmed — switches presentation to `OverFullScreen` but iOS still treats it as a separate window for focus purposes).

## Durable fix: refactor off `<Modal>` to root-level `Animated.View` overlay

Same View tree as the rest of the app, no separate iOS window, no focus restoration to fail. Both Scenario A and Scenario B disappear. Reference implementation: `mobile/components/Paywall.tsx` after S50 refactor.

**Pattern:**
```tsx
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { useWindowDimensions } from 'react-native';

const { height } = useWindowDimensions();
const slideY = useSharedValue(height);
useEffect(() => {
  slideY.value = withTiming(open ? 0 : height, { duration: 280 });
}, [open]);
const overlayStyle = useAnimatedStyle(() => ({ transform: [{ translateY: slideY.value }] }));

return (
  <Animated.View
    pointerEvents={open ? 'auto' : 'none'}
    style={[
      { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000, elevation: 1000, backgroundColor: Colors.background },
      overlayStyle,
    ]}
  >
    {/* SafeAreaView + content */}
  </Animated.View>
);
```

Mount at the bottom of `app/_layout.tsx` (after `<Stack>`) so it stacks above all routes.

**Tradeoffs:** Lose iOS-native swipe-to-dismiss (was already broken on `presentationStyle="fullScreen"` anyway). Need to paint your own background. Animation is JS/reanimated-driven, ~280ms feels equivalent to iOS slide.

**Side benefit:** the previous `router.back() + setTimeout(400)` workaround in `mobile/app/settings.tsx` (Session 49) for Scenario A becomes unnecessary once the destination Modal is refactored to an overlay — Settings can `openPaywall()` directly without dismissing first.

## Reproduced occurrences
- S48: Scenario A first hit (Settings → Paywall, no fix yet).
- S49: Scenario A workaround landed (`router.back() + setTimeout(400)`).
- S50: Scenario B hit (Apple Sign In → Paywall, recurring 3/3). `transparent={true}` tried, didn't help. Durable fix (overlay refactor) shipped, both scenarios resolved.
