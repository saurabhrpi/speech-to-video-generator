# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 30
**Date:** 2026-04-13
**Branch:** main
**Status:** Gallery persistence crash-proofed. Two crash root causes investigated and fixed.

## What Happened This Session
- Investigated Session 29 crash: most likely cause is react-native-reanimated native worklet teardown on dev menu reload (dev-only, not production). Supported by web evidence but no .ips crash report was recovered to confirm.
- Made Gallery persistence crash-resilient: `persist()` rotates backup via `multiSet`, `hydrate()` tries primary→backup with `Array.isArray` validation, no more silent catches.
- Old Gallery data was unrecoverable (already wiped before fixes). Backup mechanism protects future data.
- Fixed second crash: save button SIGABRT from missing `NSPhotoLibraryUsageDescription` in Info.plist. Added key, ran prebuild + native rebuild.
- Found crash reports at `~/Library/Logs/DiagnosticReports/*.ips` — parsed with Python to identify TCC privacy violation.

## Next Step (ToDo's)
1. **Confirm Session 29 crash root cause.** Reproduce the dev menu reload crash, retrieve the .ips crash report, and verify reanimated frames in the stack trace. "Most likely" is not confirmed.
2. Re-test with Kling model (only Hailuo tested so far).
3. Test the recorded-audio path (only typed-prompt tested so far).
4. **Simulator paste keeps breaking.** `simpaste` alias is a workaround, not a fix. Find a permanent solution.

## Open Questions
- Will video URLs from CDN expire after app restart? MiniMax download_url expires after 1 hour. Save-to-device is the permanent solution.
