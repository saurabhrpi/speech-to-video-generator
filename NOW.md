# Session Log

## Current Session: 19
**Date:** 2026-04-07
**Branch:** main
**Status:** Stitching bottleneck SOLVED — /tmp is NBD on Replit, /dev/shm gives ~150× speedup (25 min → 15 s).

## What Happened This Session
- Diagnosed stitching bottleneck: `/tmp` on Replit is btrfs on `/dev/nbdN` (network block device). Moviepy's I/O pattern is catastrophic on NBD.
- Confirmed by reading moviepy's `ffmpeg_reader.py` source that my earlier "compose mode seeks per frame" theory was wrong — forward access is cheap.
- Applied one-line fix in `stitch_timelapse_clips`: `STITCH_TMPDIR` env var → `tempfile.mkdtemp(dir=...)`. Opt-in gate, default unchanged.
- Measured: 177 frames in 15 s on `/dev/shm` vs ~25 min on `/tmp`. Replit CPU is actually fast — NBD was hiding that.
- Saved two new memories: `reference_replit_tmp_nbd.md` (the fact), `feedback_environment_diff_first.md` (the methodology lesson).

## Next Step
1. **Stitching bottleneck — SOLVED this session** (~25 min → 15 s via `/dev/shm`). Remaining decision: production gating strategy — (a) env-var opt-in (set `STITCH_TMPDIR=/dev/shm` in Replit Secrets) or (b) auto-detect `/dev/shm` + size-aware fallback to `/tmp` (safer at full-pipeline scale — /dev/shm is only 64 MB, full 7-stage pipeline ~25-30 MB peak, tight).
2. User to decide commit scope: tmpfs fix alone, bundled with pre-existing `i2v_duration` fix, or also with frontend `NUM_STAGES=7` hardcode fix.
3. Parallelize transition I2V generation (`video_service.py:562-664`) — now the biggest remaining bottleneck; trivially parallelizable with ThreadPoolExecutor.

## Open Questions
- Production gating strategy for `STITCH_TMPDIR` (opt-in vs auto-detect with fallback).
- Frontend `NUM_STAGES = 7` hardcoded in `mobile/lib/constants.ts` — mini pipeline UX still broken.
- Bleed audit marks bled elements as "renovated" causing early exit (deferred).
- expo-av deprecated in SDK 54, removed in SDK 55 — plan migration to expo-video.
