# Kling MC limitations — sources/choreographies Kling can't deliver (running log)

Running log of motion-transfer sources that **Kling Motion Control cannot deliver a usable result for**, with failure mode + root cause + decision for each. Scan this when sourcing future templates so we don't re-attempt known-bad choreography. We do **not** open a Linear ticket per failure — instances live here; AIV-103 just points to this doc.

**The general rule (learned):** Kling MC reliably reproduces only **upright, camera-facing, full-body, unoccluded** choreography with **non-contradictory body translation**. It fails two ways:
- **(a) drops/rejects untrackable poses** — floor / back-to-camera / occluded. Needs ≥3s continuous *valid* (trackable) motion or it drops frames (short, choppy output + limb hallucination) or hard-rejects.
- **(b) overrides body translation that contradicts its walking prior** — depth-axis moonwalk (feet walk forward → body slides backward) gets flipped to normal walking.

**The two responses to any instance here:** re-source the choreography (upright/camera-facing), or move it to a non-Kling model — see Linear **AIV-109** (evaluate a non-Kling motion-transfer model; competitor evidence says floor choreography IS doable).

Related: `memory/reference_kling_min_continuous_valid_motion.md`, `memory/reference_kling_driver_quality_checklist.md`, `memory/reference_viggle_own_model.md`.

## Summary

| # | Source | Failure mode | Root cause | Decision |
| -- | -- | -- | -- | -- |
| 1 | **Bad** (HubX moonwalk) | Generates, but inverts depth-axis (moonwalk → normal walk) | "feet walking → body moves forward" prior overrides source's backward translation | Re-source (Bad-*walk* not moonwalk), Kling I2V, or non-Kling (AIV-109) |
| 2 | **River** (competitor floor dance) | Can't track floor poses → drops them (short, choppy + extra hand) or rejects segment | Floor/reclining/back-to-camera/occluded poses aren't "valid motion"; needs ≥3s continuous valid | Abandon source; replace with upright Girl Dance, or non-Kling (AIV-109) |

---

## Instance 1 — Bad: depth-axis moonwalk inversion (S75)

### Symptom
Kling MC inverts the depth-axis body translation. The source (HubX's AI-generated 13s moonwalk) has the dancer's body sliding BACKWARD across the floor while feet do heel-toe forward articulation — the canonical moonwalk illusion. Every Kling MC output shows the body sliding FORWARD instead, breaking the illusion (looks like normal walking).

### Root-cause hypothesis
Kling MC carries a strong prior: *"feet doing walking-like articulation → body translates in the walking direction."* The moonwalk deliberately contradicts that prior; Kling overwrites the source's backward translation. The depth axis appears to be the only axis with this failure — lateral motion templates (Bombale, Gangsta, Baby Dance, Beat It, Smooth Criminal, Thriller, No Batidão, Rasputin, Boot Stop Working) all faithfully preserve direction.

### Experiments tried — all failed
Six Kling runs (~$10 total), all on the same NBP-edited character image (`bad_open_edit_df14566f.jpg` — clean rooftop, no mirrors, lots of lateral space):

| # | Config | Result |
| -- | -- | -- |
| 1 | v2.6 pro, generic prompt, NBP chef-kitchen scene | Body forward + distortion artifacts |
| 2 | v2.6 pro, generic prompt, rooftop scene | Body forward (distortion fixed) |
| 3 | v3 pro, generic prompt, rooftop | Body forward |
| 4 | v2.6 pro, prompt-steered ("body translates BACKWARD") | Body forward |
| 5 | v2.6 pro, compound time-flip (reverse driver → Kling → reverse output) | Body forward |
| 6 | v3 pro + prompt-steered (combined) | Body forward |

The prior is not steerable via model choice, prompt language, or input time-reversal.

### Assets
- Source MP4: `https://assets.speech-2-video.ai/viral-dances/bad-chef/driving_video.mp4` (HubX, 15s trimmed, 1284×1380, audio)
- NBP character: `/Users/saurabhsmacbookair/Downloads/bad_open_edit_df14566f.jpg`
- Chain script: `scripts/test_bad_open_chain.py`
- Slug `viral-dances-bad-open` staked, never seeded/published. Original `viral-dances-bad` (S70 wardrobe-swap variant) still live.

### Fix paths (in order)
1. **Kling I2V** (image + text prompt instead of driving video) — MJ moonwalk may be in training corpus. ~$1-2/attempt.
2. **Substitute source** — the iconic MJ "Bad walk" is a lateral swagger-step (normal footwork), NOT a moonwalk → dodges the prior.
3. **Non-Kling provider** → AIV-109.
4. **Drop Bad** — do-nothing; MJ Dances row ships Beat It + Smooth Criminal + Thriller without it.

Cost ceiling: if path 1 fails on first attempt (~$2), de-prioritize; don't burn another ~$10.

---

## Instance 2 — River: floor/occluded choreography fails the ≥3s-continuous-valid-motion check (S79)

### Symptom
River source = competitor-app floor dance (reclining, kneeling, low crouches, back-to-camera, hands-on-ground; phone screen-grab). Full 14.55s driver → output **7.2–9.27s, temporally choppy** (deduction scattered across the clip, not a tail-cut) **+ hallucinated extra hand** near the end.

### Root cause — confirmed by Kling's own error
Feeding an isolated **t=3–6s** segment (contains a bent-forward / head-down floor pose) → hard rejection:

> `The input was rejected, The duration of continuous valid motion is too short; it should last at least 3 second.`

Kling MC requires ≥3s of continuous *valid (trackable)* motion. Floor/occluded poses aren't trackable → dropped (full driver → short+choppy+limb hallucination) or rejected (isolated <3s-valid segment).

### Experiments tried — all failed
Same character image (`river_edit_cropzoom_v1.jpg`), driver `viral-dances/river/driving_video_2k.mp4`:

| # | Config | Result |
| -- | -- | -- |
| 1 | v2.6 pro, original-res driver (1284×1380, 41.89fps) | 11.97s, choppy |
| 2 | v2.6 pro, 2k Topaz upscale (2568×2760, 41.89fps) | 7.2s, choppy |
| 3 | v2.6 pro, 2k + 30fps normalized | 9.27s, choppy + extra hand |
| 4 | **v3** pro, 2k + 30fps (A/B vs #3) | **9.266s — identical to v2.6** |
| 5 | v2.6 pro, first-3s segment (trackable reclining→kneeling) | near frame-perfect, 2.93s ✓ |
| 6 | v2.6 pro, next-3s segment (t=3–6, floor pose) | **REJECTED** (error above) |

Resolution, fps, and model are NOT the lever (v2.6 ≡ v3 to the frame; upscale/fps only shuffled duration). Choreography trackability is. The Hills (upright, camera-facing) tracked clean: 15.77s → 15.3s.

Segmentation/parallel can't rescue this: a bad pose fails in *any* segment containing it (instance #2, run #6 proves it).

### Decision
**River source abandoned (S79).** Clip-killer extra hand + choppiness fail the quality bar; no encoding/model change fixes an untrackable source. Replace with an upright, camera-facing Girl Dance source, or drop the slot.

### Assets
- Character: `/Users/saurabhsmacbookair/Downloads/App Templates Prep/river_edit_cropzoom_v1.jpg`
- Drivers on R2: `viral-dances/river/raw_source.mp4` (orig 12.8MB), `.../driving_video_2k.mp4` (2k/30fps), `.../driving_video_3s.mp4` + `.../driving_video_3s_seg2.mp4` (segment tests)
- Chain script: `scripts/test_river_chain.py`. Slug staked, never seeded/published.
