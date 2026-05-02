---
name: React Navigation v7 back button label
description: In Expo SDK 54 / React Navigation v7, `headerBackTitle: ''` is silently ignored. Use `headerBackButtonDisplayMode: 'minimal'` to hide the back button label.
type: reference
---

In Expo SDK 54 (React Navigation v7), the old `headerBackTitle: ''` / `headerBackTitleVisible: false` props are silently ignored on the native iOS stack. The back button keeps showing the previous screen's title (or the route name like `(tabs)`) regardless.

The working prop is `headerBackButtonDisplayMode`. Valid values: `'default'` | `'generic'` | `'minimal'`. Use `'minimal'` to render only the chevron without any label.

Apply on the screen being navigated TO (the one whose header shows the back button), either inline or in the layout registration:

```tsx
// mobile/app/_layout.tsx
<Stack.Screen
  name="clip/[id]"
  options={{ title: 'S2V', headerBackButtonDisplayMode: 'minimal' }}
/>

// or inside the screen component
<Stack.Screen
  options={{
    title: 'S2V',
    headerBackButtonDisplayMode: 'minimal',
    headerRight: () => <TrashButton />,
  }}
/>
```

When the back button label looks wrong (e.g., shows `(tabs)`), this is almost always the fix — not a route-naming or title-cascading issue.
