# Interior Timelapse — V2 Backlog

Archived from NOW.md on 2026-04-11 when the app pivoted to Speech-to-Video MVP (session 24).
Everything below was the live Interior Timelapse state before Interior Timelapse was demoted to V2.
Pick up from here when V2 work resumes.

---

## Diagnostic state at time of archive

**AIMLAPI I2I slowness definitively confirmed as upstream** — T2I fast, network fine, I2I sends headers early then dribbles a 169-byte chunked body for ~4 min.

Diagnostic run captured in `debug/logs.txt`. Parsed results:
- socket 194 ms
- cdn_fetch 1.65 s
- t2i 21.6 s (TTFB 21.6 s / body 0 ms)
- **i2i 287.3 s (TTFB 51.6 s / body download 235.7 s for 169 bytes, Transfer-Encoding: chunked)**
- Stage 3 I2I in the real pipeline reproduced exactly 4:45.

Rules out: our retry ceiling, client, network, DNS, TLS, CDN, screen-sleep, container restart. The bottleneck is AIMLAPI holding the chunked response open upstream. See `memory/reference_aimlapi_i2i_latency.md` so future sessions don't re-diagnose.

## ToDo backlog (ordered, roughly by priority)

1. **Delete `RUN_STARTUP_DIAGNOSTIC` from Replit Secrets** (Tools → Secrets → trash icon). Otherwise the diagnostic re-runs on every boot/autoscale, burning a ~$0.39 I2I credit each time. **(Still pending as of pivot — do this even if you don't touch timelapse again soon.)**
2. **Attempt a direct Google Gemini API integration for I2I** to see if it bypasses the ~4:45 bottleneck — `generativelanguage.googleapis.com`, Nano Banana Pro Edit equivalent model. Keep T2I on AIMLAPI for now (~22 s is fine). New env var `GEMINI_API_KEY`; new method in `AIMLAPIClient` or a sibling `GeminiClient`; wire through `video_service.py` I2I call sites only. Treat as an experiment — if direct Gemini is not materially faster, revisit the plan.
3. Parallelize transition I2V generation (`video_service.py:562-664`) — biggest remaining bottleneck once I2I is unblocked.
4. Migrate `expo-av` → `expo-video` (+ `expo-audio` if used). Verify actual removal SDK version.
5. Remove "Test SSE (fake job)" button from mobile UI.
6. Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — mini pipeline UX still broken.
7. Investigate transition I2V failure: `minimax/hailuo-02` transition 2→3 returned `{"status":"failed","error":{"message":"Unknown error"}}` after 66 s in prior run. Separate from I2I slowness.

## Open Questions

- Which Gemini model name actually maps to Nano Banana Pro Edit on the direct Google API? Verify before coding.
- Direct-Gemini pricing vs AIMLAPI — is the switch cheaper, same, or more expensive per edit?
- Bleed audit marks bled elements as "renovated" causing early exit (deferred).

## Known problems (pre-pivot frustrations — from CLAUDE.md)

1. **Transition video quality is not good enough.** Even with Kling (the expensive model), weird artifacts: half a wall left unrenovated, vents/drains "blown through" walls during transitions. Hailuo (the cheap model) is completely hallucinated garbage.
2. **Visual delta between stages is sometimes too small.** Barely noticeable consecutive keyframes → bad viewing experience.
3. **Can't reliably handle more than 2 features.** Haven't experimented beyond 2 out of fear the app can't handle the complexity.
4. **Prompt mismatch between indoor and outdoor spaces.** Prompts that work for closed rooms don't transfer to patios/outdoors.
