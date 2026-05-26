---
name: kling-min-continuous-valid-motion
description: Kling Motion Control requires ≥3s of CONTINUOUS VALID (trackable) motion in the driver. Floor/back-to-camera/occluded choreography fails — it drops untrackable stretches (→ short, choppy output + limb hallucination) or rejects outright. Pick upright, camera-facing sources at sourcing time.
metadata:
  type: reference
---

# Kling MC needs ≥3s of continuous *valid* (trackable) motion

**Core fact (S79, confirmed by Kling's own error):** Kling Motion Control validates the driving video for trackable human motion. If a submitted clip lacks a continuous trackable stretch ≥3s, it rejects with the verbatim error:

> `The input was rejected, The duration of continuous valid motion is too short; it should last at least 3 second.`

**"Valid motion" = poses Kling can pose-track:** upright, camera-facing, full-body, unoccluded. NOT reliably trackable: floor work, reclining, back-to-camera, hands-on-the-ground / heavily-occluded limbs.

## The two failure modes this produces

1. **Full-length driver with untrackable stretches scattered through it** → Kling silently **drops** the frames it can't track. Result: output is **shorter than the driver AND temporally choppy** — the loss is "scattered" (taken from the start, middle, and end), NOT a clean tail-cut. Plus **limb hallucination** (e.g. an extra hand) at the boundaries where it loses the body.
2. **An isolated short segment** whose continuous valid stretch is <3s → **hard rejection** with the error above.

## Evidence (S79 River vs The Hills)

- **River** (floor/reclining dance, phone-screen-grab source): full 14.55s driver → 7.2–9.27s output, choppy, with a hallucinated extra hand. First-3s segment (trackable reclining→kneeling) → **near frame-perfect** 2.93s. Next-3s segment (t=3–6, contains a bent-fully-forward head-down floor pose) → **rejected outright** with the error. So the choreography has untrackable stretches scattered through it.
- **The Hills** (upright, camera-facing dance): 15.77s driver → 15.3s output (~0 deduction). Clean.

## What does NOT fix it

A/B'd on the *same* driver+image: **v2.6 vs v3 → identical 9.266s**. Also tried **2k Topaz upscale** and **30fps normalization** (the odd 41.89fps → 30) — these only shuffled the duration (7.2↔9.27), never fixed the tracking or the hand. **Resolution, fps, and model are not the lever — choreography trackability is.** Don't burn Kling runs re-encoding a floor-dance driver.

## Implications

- **Selection rule (sourcing time):** choose upright, camera-facing, full-body, unoccluded choreography. Reject floor / back-to-camera / occluded sources before spending anything — Kling can't be coaxed into tracking them.
- **Segmentation/parallel can't rescue an untrackable source** — a bad pose fails in *any* segment that contains it. (For a *trackable* source, segmenting is viable as a latency play, but every segment still needs ≥3s continuous valid motion, plus an appearance-seam solution across independent gens.)

## Competitor signal (investigation pending)

A competitor app runs **full-pipeline** motion-transfer (user uploads a pic → runtime video) successfully on this *exact* floor choreography. That means a **non-Kling model/technique** handles complex/floor/occluded poses that Kling MC cannot. Worth reverse-engineering — see the River AIV ticket and the competitor-model research spike. Candidates to evaluate: Viggle, Runway Act-Two, Wan animate, etc.

Related: [[no-overfit-prompts]]. Sibling Kling-MC limitation: AIV-103 (Bad — depth-axis moonwalk inversion).
