---
name: rn-scrollview-pointerevents-ignored-by-pan-gesture
description: RN ScrollView's native UIScrollView pan-gesture recognizer ignores React's pointerEvents entirely. Touch routing in overlapping-ScrollView layouts (sticky/slider-phone heroes, parallax headers, drawers) requires react-native-gesture-handler — pointerEvents cannot deny vertical drags to a ScrollView frame.
metadata:
  type: reference
---

In React Native, `pointerEvents` (`auto` / `none` / `box-none` / `box-only`) only controls **React's JS-side hit testing** — which view "owns" a touch from React's perspective. The native iOS `UIScrollView` pan-gesture recognizer is attached at the native level and observes touches within its frame **regardless** of any RN-side pointerEvents config.

Consequence: in any layout where a ScrollView's frame overlaps another touchable area (sticky hero, slider-phone hero, parallax header, custom modal under a list), the ScrollView will grab vertical drags in the overlap region. Setting `pointerEvents="box-none"` on the spacer, the scroll content, or the ScrollView itself does **not** fix this. The overlapping touchable area is starved of vertical-drag input — horizontal swipes and taps may also be lost because the ScrollView's native hitTest still routes them.

**Why:** S71 — ~2 hours trying to ship a slider-phone hero on `mobile/app/index.tsx` (sticky hero + content slides OVER on scroll). Five layered fixes all failed:

1. `Animated.event` with `useNativeDriver: true` driving a dim overlay → listener callback swallowed.
2. Same with `useNativeDriver: false` → listener fired but the fake dim overlay didn't visually convince (we wanted real obscuration).
3. Absolute layering: heroLayer behind, ScrollView on top with transparent spacer + opaque content → content slid OVER hero visually ✓, but ScrollView's frame swallowed hero touches ✗.
4. Same plus `pointerEvents="box-none"` on the spacer → no change.
5. Same plus `pointerEvents="box-none"` on the ScrollView itself → no change.

User's diagnostic comment that closed it: *"even if i touch at the top of the screen at the top of the hero, i m able to move the content below. Looks like the input starvation is real for hero."* Reverted to plain hero-inside-ScrollView. Tracked as AIV-99 with two viable paths for future: (a) conditional z-index swap based on scrollY threshold, (b) `react-native-gesture-handler` custom scroll with `reanimated` worklets for momentum.

**How to apply:** Before designing any layout where touch routing crosses a ScrollView boundary, plan for `react-native-gesture-handler` from the start. Don't rely on `pointerEvents` to deny touches to a ScrollView — it cannot. Native gestures live in a different layer than React's hit testing. `gesture-handler` and `reanimated` are already in `mobile/package.json` (~2.28.0 and ~4.1.1); use them. Pairs with [[absolute-overlay-button-intercept]] (same family of "RN touch routing surprises") and [[ios-modal-on-modal]] (other RN gesture quirks).
