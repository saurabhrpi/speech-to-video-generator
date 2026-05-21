---
name: video-motion-needs-human-eye
description: Don't diagnose video motion characteristics (camera static vs panning, subject anchored vs gliding) from frame snapshots — subject translation aliases as camera motion in stills.
metadata:
  type: feedback
---

When diagnosing **motion characteristics** of a video (is the camera moving vs static, is the dancer gliding vs moonwalking, is the subject anchored to the ground, is the motion smooth), don't substitute extracted frame snapshots + pixel-diff comparison for actually watching the video. Defer to a human eyeballing it, or run a proper video-analysis tool (optical flow, ffmpeg `vidstabdetect`, motion-vector dump).

**Why:** S71 Bad template iteration. User asked why the Kling output had apparent camera motion when "the original was static." I extracted frames at t=0.2 and t=9.5, observed that the background composition was very different (new doorway visible, kitchen island at a different angle), and confidently declared "the camera is not static." The user corrected me sharply: "That's not a camera movement, you fool. That's because the dancer has shifted. The dancer starts from one end and moonwalks their way to the other. Of course they will be in a different position relative to the camera." As the subject translated past a fixed camera, different parts of the room were revealed/occluded — background-reveal in snapshots reads as camera motion but is actually subject translation. Trust + iteration time lost.

**How to apply:** Snapshot comparison is reliable for *content* questions (what's in the scene, what the subject is wearing, what the framing looks like, whether there are baked-in UI overlays). It is NOT reliable for *motion* questions. For motion questions: ask the user to eyeball, or run proper video analysis. Especially treacherous when the subject translates across the frame — snapshot diff and camera motion are aliased and indistinguishable from stills alone. Pairs with the reverse trap in [[kling-driver-quality-checklist]]: static camera IS the load-bearing requirement for Kling Motion Control, but you cannot verify it by looking at frame stills.
