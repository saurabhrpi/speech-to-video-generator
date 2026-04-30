---
name: NativeWind + Pressable function-form style silently drops styles
description: When using Pressable with NativeWind className present elsewhere in the tree, the function-form `style={({ pressed }) => ({...})}` does NOT apply — backgrounds/borders/sizes silently fail to render. Use plain object `style={{...}}` instead. Verified S52 by direct A/B test on sim.
type: reference
---

When using Pressable in a NativeWind-enabled tree, the function-form `style={({ pressed }) => ({...})}` may not be evaluated for the initial render — resulting in NO inline styling applied at all (no background color, no width/height, no border). The button collapses to its children's natural size and only the inner icons/text are visible.

**S52 verified burn:** I wrote a Pressable like this:
```tsx
<Pressable
  onPress={...}
  style={({ pressed }) => ({
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: '#2563EB',
    opacity: pressed ? 0.85 : 1,
    ...
  })}
>
  <Ionicons name="mic" size={56} color="#FFFFFF" />
</Pressable>
```

Result on the rebuilt sim: just the white mic icon with no blue circle around it. The 130×130 button + blue background + border were silently absent. Switching to plain object `style={{...}}` rendered the blue circle correctly on the same rebuild — A/B confirmed.

**Verified working pattern in this codebase** (Paywall.tsx, gallery.tsx, and now mobile/app/(tabs)/index.tsx all use this and render correctly):
```tsx
<Pressable
  onPress={...}
  style={{
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: '#2563EB',
    alignItems: 'center',
    justifyContent: 'center',
  }}
>
  <Ionicons name="mic" size={56} color="#FFFFFF" />
</Pressable>
```

**How to apply:**
- For any new Pressable in this codebase, default to plain object `style={{...}}`.
- Pressed-state visual feedback is a nice-to-have; haptic feedback on tap usually communicates enough on its own.
- If pressed-state animation is required, use `Animated.createAnimatedComponent(Pressable)` with a sharedValue driven by `onPressIn`/`onPressOut` (the existing `Button.tsx` already follows this pattern with `react-native-reanimated`).
- If a Pressable "looks unstyled" after writing it (icons/text visible but no background or sizing), the function-form style is the first place to check.
