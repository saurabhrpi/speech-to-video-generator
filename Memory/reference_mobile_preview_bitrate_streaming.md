---
name: Mobile template previews need ~5 Mbps streaming encode
description: Raw Kling preview output (14-35 Mbps @ 1440²) stutters on mobile; serve a ~5 Mbps + faststart copy, decoupled from the driver
metadata:
  type: reference
---

Raw Kling Motion Control output is **14-35 Mbps @ 1440×1440** (S77 catalog: dance-flow ~35, na-favelinha ~25, mapopo ~23). Serving that straight to the mobile app's looping `<Video>` tiles causes **start-stop / rebuffer stutter** — the phone can't sustain the bandwidth, the buffer drains, playback pauses. The symptom is the bitrate, not the file size, and it compounds on the home grid (multiple concurrent decodes). Also: raw Kling mp4s may lack `+faststart` (moov at end → player waits for full download before playing), which alone causes start-stop.

**Fix (locked S77, catalog-wide):** serve a **~5 Mbps + faststart** H.264 copy (`preview_stream.mp4`) as `preview_video_url`. Built/repointed/reverted via `scripts/streaming_previews.py` (`--encode` / `--repoint` / `--revert`). Verified on iPhone: smooth.

**Decouple from the driver (critical nuance):** under preview-as-driver the preview file ALSO doubles as the runtime Kling driver, and Kling degrades on low-bitrate input. So do NOT recompress the preview in place — keep the high-bitrate file as the driver and serve a SEPARATE low-bitrate `preview_stream.mp4` to the app. S77 then renamed R2 files to match roles (`migrate_driver_filenames.py`): `raw_source.mp4` (source/revert) / `driving_video.mp4` (high-bitrate driver) / `preview_stream.mp4` (app). Full shape + going-forward steps in `docs/V2_template_creation_runbook.md` (S77 section). Filenames are URL-driven via Firestore fields — never delete a file by its name (`driving_video.mp4` is the load-bearing driver). Orphan cleanup tracked in AIV-107.
