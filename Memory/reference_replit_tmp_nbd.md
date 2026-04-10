---
name: Replit /tmp is NBD
description: Replit /tmp is mounted on a network block device; I/O-heavy ops like video stitching can be ~150x slower there than on /dev/shm tmpfs
type: reference
---

On Replit, `/tmp` is btrfs on `/dev/nbdN` — a network block device. Every read/write is a TCP round trip to a remote storage host. Mount options (`nobarrier,noatime,ssd,space_cache=v2`) tune it as much as possible in software, but the transport is still network.

**Measured impact on this project** (moviepy stitch of ~6s output from 2 short source clips):
- `/tmp` (NBD): ~25 min (≈12 s/frame)
- `/dev/shm` (tmpfs, RAM): ~15 s (≈0.085 s/frame)
- ~150× faster, same code, same machine, only the temp directory changed

**`/dev/shm` on Replit:** real `tmpfs`, but only **64 MB**. Enough for a mini-pipeline stitch; tight for the full 7-stage pipeline (~25-30 MB peak source+output); will overflow at higher resolution/bitrate. Always gate with a fallback plan for `ENOSPC`.

**Important negative finding:** Before measuring, I spent multiple turns theorizing that moviepy's compose mode was seeking per frame. Reading moviepy's `ffmpeg_reader.py` disproved that — forward access uses `skip_frames`, no reinit. Moviepy is NOT slow; the NBD transport is. Whatever I/O pattern moviepy does was pathological for NBD specifically. Don't blame moviepy when you see similar symptoms here.

**Check with:** `mount | grep /tmp`, `df -h /dev/shm`, `ls -la /dev/shm`.

**Rule of thumb:** any I/O-heavy workload on Replit (video processing, archive extraction, many small file ops) should use `/dev/shm` when it fits and fall back to `/tmp` otherwise. Surprisingly, Replit's CPU on tmpfs is actually *faster* than a Mac at this specific workload — NBD was hiding perfectly good compute.
