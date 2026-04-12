---
name: NativeWind dynamic styles
description: Use inline style prop (not dynamic className) for conditional active/inactive states in React Native + NativeWind
type: feedback
---

For conditional styles that toggle on user interaction (active/inactive tabs, selected/unselected), use inline `style` prop instead of dynamic NativeWind classNames (ternaries or template literals).

**Why:** NativeWind processes classNames at build/transform time. Dynamic classNames combined with hot reload can cause stale cache and render crashes (seen as "Couldn't find navigation context" errors that are actually downstream of a render failure). Clearing Metro cache (`--clear`) fixes it temporarily, but inline styles avoid the issue entirely.

**How to apply:** Keep static layout classes (`items-center rounded py-2`) on NativeWind `className`. Move dynamic visual states (backgroundColor, shadow, text color for active/inactive) to `style` prop.
