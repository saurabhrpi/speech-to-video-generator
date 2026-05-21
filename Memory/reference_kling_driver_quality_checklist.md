---
name: kling-driver-quality-checklist
description: Pre-Kling checklist for Pipeline A driving videos + NBP character images. #1 (static camera) is the load-bearing requirement — everything below is incremental. Lessons from 5 Beat It iterations (S70).
metadata:
  type: reference
---

**TL;DR:** #1 (static camera) is the only hard requirement. Items 2-6 are incremental — each helps a bit, none of them save you if the camera is moving. In the Beat It S70 iterations, 4 of 5 reruns tuned items 2-6 against a slightly-handheld source and never got grounded output; switching to a fully-static-camera source got it on the first try, even with items 5 and 6 violated (text overlay present, dimmer scene). Verify item 1 first; only fall through to 2-6 once camera motion is ruled out.

## 1. STATIC CAMERA (load-bearing — the only hard requirement)

The driving video's camera **must not move**. No handheld shake, no panning, no zoom, no follow-cam. Kling Motion Control derives the ground plane and scene anchors from the driving video frame-by-frame. If the camera moves, the ground plane shifts under the character every frame → output character appears to float, slide, or feel "photoshopped in" even when everything else is correct.

**S70 lesson:** the no-watermark Beat It source had subtle handheld shake. Output dancer never felt fully grounded across multiple NBP iterations (alley, indoor industrial loft) — the floor "moved differently" than expected. Switching to a different YT source with a fully static tripod camera fixed it in one run, even though that clip had a large LCD playing the original Beat It MV in 35% of the frame.

**Fix:** when sourcing, prefer single-take phone-on-tripod clips. Reject anything handheld, gimbal-walked, drone, or with visible reframing. This is non-negotiable — fixing the other 5 items doesn't compensate for camera motion.

## 2. Driving video resolution ≥ 720×1280 (incremental)

Higher source res gives Kling more pose detail. TikTok downloader sites (TikWM, SnapTik) silently serve 576×1024 for some clips even when the upstream was 1080p — verified S70 for Beat It, Smooth Criminal, Bad. Pinky Up and Rasputin came back at 1080×1920 from the same sites.

Low-res input correlates with "jacket disappears" / "limb tracking lost" symptoms, but in the S70 reruns these symptoms persisted even after upscaling to 1080×1920 — the real culprit was item #1. Worth upscaling anyway when easy: `scripts/upscale_driving_video.py` (Replicate `lucataco/real-esrgan-video` → FHD). ~$0.02-0.05, ~4 min.

## 3. Baked-in text overlays / watermarks (often fine to leave)

TikTok downloads often have:
- TikTok logo + username (often BOUNCES position to defeat static `delogo`)
- Caption text ("channeling that MJ energy" etc., usually static at top-center)
- Other creator-added overlays

These *can* produce overlay-smear artifacts in Kling output, but the accepted Beat It final used a source with a visible 35%-of-frame LCD playing the original MV and Kling 2.6 handled it cleanly. **Don't preemptively mask** moving competing-subject elements; try the unmasked clip first and only mask if Kling actually bleeds them in.

If you do need to remove an overlay, prefer (in order): (1) re-download with a "no-watermark" option, (2) source from a different platform (YouTube original etc.), (3) `delogo` only when the overlay is small + on a uniform background + the subject never crosses the box.

## 4. Ground-plane match between NBP scene and driving video (incremental)

When the driving video has a flat horizontal floor (parquet, hardwood, polished concrete), a similar floor in the NBP character image reduces "floating" perception. The effect is real but secondary to item #1 — on a static-camera source even an imperfect ground-plane match looks acceptable; on a moving-camera source even a perfect match still floats.

If you're tuning the NBP edit prompt anyway, match the floor: indoor driving video → indoor NBP scene with hardwood/parquet; outdoor concrete → outdoor concrete.

## 5. Subject vs. background contrast in the NBP edit (incremental)

Dark outfit on dark background can produce silhouette-loss artifacts (jacket-disappears, limb-melts) during heavy motion. The S70 Beat It v1 used black bomber + dark jeans on a dusk graffiti alley; output was unusable. Same outfit on a brighter indoor loft → fine.

Not a hard rule — many published templates use moody scenes successfully. But if you're iterating on the NBP prompt anyway, ensure the subject's edges read clearly against the background. Avoid extreme dark-on-dark or light-on-light combinations.

## 6. `delogo` box sizing — tight, not generous (only relevant if you're delogo-ing)

If you do reach for `delogo`, size the box tightly to the text region. Generous padding leaks into surrounding scene elements (ceiling fixtures, smoke detectors, wall art) which smear visibly under motion. And `delogo` has no concept of person vs. background — if any dance move extends INTO the text's vertical band, the filter will paint over the limb at peak frames.

If the text is on a clean uniform region AND the subject doesn't enter the box, `delogo` is invisible. Otherwise prefer re-sourcing (item #3) over filtering.

## Workflow that avoids the iterations

1. **Reject moving-camera sources at intake.** Single hardest filter; everything else is fine-tuning. If the camera is moving even slightly, find a different source — don't waste a Kling iteration trying to compensate.
2. Probe source resolution → optionally upscale if <720 wide.
3. Watch the driving video — note floor material + lighting register for the NBP prompt.
4. Write NBP edit prompt; iterate on the still with `--no-kling` until character + scene are right.
5. Only then run Kling. If output still floats and items 2-5 are fine, **re-verify the source camera is actually static** — this was the trap on Beat It.
