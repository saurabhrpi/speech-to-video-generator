# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 29
**Date:** 2026-04-12
**Branch:** main
**Status:** Direct MiniMax client built and working. Hailuo 2.3 generates videos successfully. Gallery UX polished.

## What Happened This Session
- Built `minimax_client.py` — bypasses AIMLAPI, hits MiniMax API directly (submit/poll/download). Wired into VideoService for Hailuo models.
- Tested end-to-end: Hailuo 2.3 via direct MiniMax API generates videos successfully from the mobile app.
- Gallery UX: save tracking (saved flag + checkmark replaces download button), failed jobs auto-removed with alert instead of error cards, X remove button on completed cards (visible only when selected), tap empty space to deselect, generating jobs persisted for app-close recovery with SSE reconnect on hydrate.
- Speech tab: Hailuo (6s) now default model, shown first. Title font changed from Playfair to Inter.

## Next Step (ToDo's)
1. **App crashed on reload** — cause unknown. Pressable wrapping FlatList and missing `saved` field were investigated but neither confirmed as root cause. Need to reproduce and debug.
2. Re-test with Kling model (only Hailuo tested so far).
3. Test the recorded-audio path (only typed-prompt tested so far).
4. **Simulator paste keeps breaking.** `simpaste` alias is a workaround, not a fix. Find a permanent solution.

## Open Questions
- Will video URLs from CDN expire after app restart? MiniMax download_url expires after 1 hour. Save-to-device is the permanent solution.
- What caused the app crash on JS reload? Not reproducible yet.
