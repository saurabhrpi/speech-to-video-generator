# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. Do not remove ToDo's unless user says.

## Current Session: 23
**Date:** 2026-04-10
**Branch:** main
**Status:** SSE auto-reconnect works. Discovered I2I edit calls are stuck at exactly ~4:44 per call (regression from <60s a few days ago). Diagnostic endpoint added, not yet run.

## What Happened This Session
- Tested previous SSE heartbeat fix → failed. Comment heartbeats get ignored by proxies; stream dropped during long I2I. Replaced with real `data:` event heartbeat every 10s + frontend auto-reconnect (up to 20 retries) in `streamJob`.
- Re-tested: reconnection works (UI shows "Reconnecting..." between stages) but surfaced the real bottleneck — every Nano Banana Pro Edit call takes exactly 4m 44s. Same pattern across 3+ sessions, suspiciously uniform.
- Confirmed no recent code change touches `aimlapi_client.py` — this is external (AIMLAPI-side or Replit→AIMLAPI network). User says locally it was <60s, Replit was fast a few days ago.
- Added `GET /api/debug/time-image-edit` — runs socket/DNS/TCP/TLS probe + CDN fetch + T2I baseline + I2I call from inside deployed container, logs every probe to Replit logs so data survives if proxy kills the 5+ min response.
- Caught 2 bugs in the diagnostic endpoint before push: undefined `logger` and missing `Dict`/`Any` imports.

## Next Step (ToDo's)
1. **Push + set `RUN_STARTUP_DIAGNOSTIC=1` in Replit secrets + Republish.** Diagnostic runs automatically in a background thread on container boot. Wait ~5.5 min, read the 4 probe results from Replit logs (`[DEBUG time-image-edit]` lines). Interpret: if `i2i_probe.time_to_headers_ms` ≈ 4 min but others fast → AIMLAPI holds the request → consider switching I2I to direct Google Gemini API.
2. **After step 1 results are captured, DELETE `RUN_STARTUP_DIAGNOSTIC` from Replit secrets.** Otherwise the diagnostic will re-run on every container restart/auto-scale and burn ~$0.10 + 5min AIMLAPI load each time. To delete a secret: Replit → Tools → Secrets → find `RUN_STARTUP_DIAGNOSTIC` → click the trash/delete icon next to it.
3. Parallelize transition I2V generation (`video_service.py:562-664`) — biggest remaining bottleneck once I2I is unblocked.
4. Migrate `expo-av` → `expo-video` (+ `expo-audio` if used). Package says "removed in SDK 54" — verify actual removal version.
5. Remove "Test SSE (fake job)" button from mobile UI.
6. Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — mini pipeline UX still broken.
7. Full pipeline review screen bug (ToDo #1 from last session) — resolved by SSE auto-reconnect.

## Open Questions
- Why did Nano Banana Pro Edit go from <60s to 4:44 exactly? AIMLAPI regression, account throttling, or Replit IP block?
- If confirmed AIMLAPI-side, is the right move a direct Google Gemini API integration for I2I, or try another reseller?
- Bleed audit marks bled elements as "renovated" causing early exit (deferred).
