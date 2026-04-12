# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.
> **V2 backlog:** Interior Timelapse work was archived to `INTERIOR_TIMELAPSE_V2_BACKLOG.md` during the session-24 pivot. Read that when Interior Timelapse work resumes.

## Current Session: 26
**Date:** 2026-04-11
**Branch:** main
**Status:** Speech-to-Video pipeline fully working on mobile (Hailuo tested, video plays). Design PRD plan written, ready to implement.

## What Happened This Session
- Fixed VideoPlayer timeout: replaced fixed 30s timer with URL verification (GET Range:bytes=0-0) + 90s safety net. Discovered AIMLAPI CDN (Alibaba OSS) rejects HEAD on signed URLs — signature is method-specific.
- Added wake lock (expo-keep-awake) to Speech tab — screen was sleeping during generation, killing SSE.
- Added auth to Speech tab: gear icon in header linking to Settings, `canGenerate()` gate, "Sign in required" banner. Was missing after the pivot.
- Added `simpaste` alias to ~/.zshrc for simulator clipboard workaround.
- Wrote Design PRD implementation plan at `design/SPEECH_TAB_DESIGN_PLAN.md`.

## Next Step (ToDo's)
1. **Implement Design PRD on Speech tab.** Plan is at `design/SPEECH_TAB_DESIGN_PLAN.md`. Phase 1: colors + fonts, Phase 2: shared components, Phase 3: Speech tab restyle.
2. Re-test with Kling model (only Hailuo tested so far).
3. Test the recorded-audio path (only typed-prompt tested so far).
4. **Simulator paste keeps breaking.** `simpaste` alias is a workaround, not a fix. Find a permanent solution.

## Open Questions
- Will NativeWind support custom `fontFamily` via className, or will Playfair Display need inline styles?
