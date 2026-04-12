---
name: CTFontManagerError 104 is safe
description: expo-font throws on error 104 (already registered) but the font IS usable — catch and treat as success
type: reference
---

CTFontManagerError code 104 = font already registered with Core Text. This happens when:
- The font was registered in a previous app load (Expo Go retains registrations across reloads)
- The font is a system font (e.g., Inter on iOS 17+)

The font IS available despite the error. Fix: catch error 104 in the `useFonts` error handler and treat it as success instead of throwing.

Also: Inter is a built-in system font on iOS 17+ — don't bundle or register it via expo-font. Just reference `Inter` / `Inter-Medium` by name in tailwind config.
