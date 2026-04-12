# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.
> **V2 backlog:** Interior Timelapse work was archived to `INTERIOR_TIMELAPSE_V2_BACKLOG.md` during the session-24 pivot. Read that when Interior Timelapse work resumes.

## Current Session: 27
**Date:** 2026-04-12
**Branch:** main
**Status:** Design system implemented on Speech tab. Gallery tab planned, not yet built.

## What Happened This Session
- Implemented the Design PRD (all 3 phases) from `design/SPEECH_TAB_DESIGN_PLAN.md`:
  - Phase 1: Warm dark palette in global.css, Playfair Display via @expo-google-fonts, type scale + border radii + elevated color in tailwind config, design-tokens.ts + utils.ts created.
  - Phase 2: Button got spring press animation (0.96x Reanimated) + rounded-button radius + glassy borders. VideoPlayer spinner and ConfirmModal elevated bg updated.
  - Phase 3: Custom WarmDarkTheme for React Navigation, gold tab/header tints, full Speech tab restyle (Playfair heading, Inter body, uppercase section labels, card-colored inputs, 20px padding, 32px gaps).
- User then changed accent from gold to dark shade (#2E2724) with glassy semi-transparent white borders (rgba 255,255,255,0.18). Tab icons/gear changed to linen-white.
- Handled CTFontManagerError 104 — font already registered treated as success instead of crash. Inter is a system font on iOS 17+, no need to bundle.
- Planned Gallery tab to replace Video Studio: non-blocking generation, 2-column grid of video thumbnails, save-to-Camera-Roll. Plan at `design/GALLERY_TAB_PLAN.md`.

## Next Step (ToDo's)
1. **Implement Gallery tab.** Plan is at `design/GALLERY_TAB_PLAN.md`. Install deps, create gallery store, create gallery screen, modify Speech tab to fire-and-forget, update tab layout, delete video-studio.tsx.
2. Re-test with Kling model (only Hailuo tested so far).
3. Test the recorded-audio path (only typed-prompt tested so far).
4. **Simulator paste keeps breaking.** `simpaste` alias is a workaround, not a fix. Find a permanent solution.

## Open Questions
- NativeWind fontFamily via className works for Playfair Display (answered: yes, via tailwind config fontFamily mapping to registered font name).
- Will video URLs from CDN expire after app restart? Gallery persists URLs in AsyncStorage but they may 404. Save-to-device is the permanent solution.
