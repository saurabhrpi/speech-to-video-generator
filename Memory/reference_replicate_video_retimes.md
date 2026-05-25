---
name: Replicate Real-ESRGAN video re-times the clip
description: lucataco/real-esrgan-video upscale changes duration/framecount → desyncs audio; re-time back before using as a Kling driver
metadata:
  type: reference
---

`scripts/upscale_driving_video.py` (lucataco/real-esrgan-video) does NOT preserve timing. S77 Mapopo: a 9.45s @ ~41fps source came back **13.81s** — the model re-extracts/reassembles frames at a different rate, ADDING frames (387 → ~566). Result: video slowed ~46%, audio desynced. The container even ends up with mismatched stream lengths.

**Fix before using the output as a Kling driver:** re-time the upscaled video back to the original duration and re-mux the ORIGINAL audio (sync then guaranteed by construction — both at original length/speed):

```bash
RATIO=$(awk "BEGIN{print ORIG_DUR/UPSCALED_DUR}")   # e.g. 9.45/13.81 = 0.6843
ffmpeg -y -i upscaled_2k.mp4 -i original.mp4 \
  -filter_complex "[0:v]setpts=PTS*${RATIO},fps=41[v]" \
  -map "[v]" -map 1:a:0 -c:v libx264 -crf 16 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart synced.mp4
```

Then push the synced file live: overwrite the R2 driver key (`r2_client.upload_file(..., key="viral-dances/<slug>/driving_video.mp4")`), **purge CF** (`scripts/purge_cf_cache.py <url>` — same-key overwrite is immutable-cached, so Kling would otherwise fetch the stale copy), then re-run the Kling chain off it. S77 Mapopo: this produced a clean **9.33s** synced output (vs the broken 13.81s-driver gen), which was published. The 2× upscale (2552²) was preserved throughout — re-encode at `-crf 16`.

**Resolution preset on a SQUARE source:** `--resolution 2k` upscaled 1284×1288 → **2552×2560** (~2×, genuine). `FHD` (=1080p) would SHRINK a source already >1080 on its short edge — so for already-decent square sources, use `2k`, not the FHD default. (S77: my "FHD shrinks it" claim was an unverified inference at the time; the 2k output dimensions confirmed the direction afterward.)

Replicate quirk recap also in [[reference_replicate_url_input_only]] (URL input only).
