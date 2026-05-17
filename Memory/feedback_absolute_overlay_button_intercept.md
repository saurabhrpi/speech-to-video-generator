---
name: absolute-overlay-button-intercept
description: When an absolute-positioned overlay Pressable on iOS doesn't receive touches at all (onPressIn never fires), refactor to flow layout instead of hunting the interceptor.
metadata:
  type: feedback
---

If a `Pressable` with `position: 'absolute'` sitting over a video/scroll/native area silently swallows all touches — `onPressIn` never fires even with `zIndex` set, `hitSlop` added, and `Stack.Screen` header hidden — **stop trying to identify what's intercepting and just move the button into flow layout.**

**Why:** S65–S66 burned three iterations on `clip/[id].tsx`'s X-overlay close button:
1. Move outside ScrollView (S65) — failed.
2. Remove `<Stack.Screen options={{ headerShown: false }} />` (S65) — failed.
3. `gestureEnabled: false` to disable iOS edge-pan (S66) — failed.

Touches still never reached the Pressable. We added on-screen `setState` diagnostics (Hermes `console.log` doesn't reach OSLog on this Expo setup, so OSLog tailing was a dead end) and confirmed `IDLE` stays after taps — RN isn't getting the event.

The fix was to refactor: replace the two `position: 'absolute'` overlay buttons with a flow-layout `headerRow` (`flexDirection: 'row'`, `justifyContent: 'space-between'`) at the top of the SafeAreaView, before the video. Both back + trash buttons immediately started working. Root cause of the intercept was never identified (candidates we didn't disprove: Paywall's root-level `Animated.View` overlay even with `pointerEvents="none"`, expo-av Video's native gesture region bleeding outside its visible bounds, something else in the GestureHandlerRootView / expo-router stack).

**How to apply:**
- iOS overlay Pressables on top of `expo-av <Video>` or above a native scroll view → first attempt should be flow layout, not absolute.
- Reserve absolute overlays for elements that genuinely *must* float over content (e.g., a play-pause icon centered on the video) and accept the risk.
- If you do need absolute, verify with on-screen `setState` diagnostic (not `console.log`) that `onPressIn` actually fires before shipping.

See also: [[ios-modal-on-modal]] (same family of "iOS native layer eats touches" issues), [[pattern-match-scenario-not-fix]] (don't pattern-match prior fixes — they didn't address the real cause).
