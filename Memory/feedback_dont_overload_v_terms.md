---
name: dont-overload-v-terms
description: V1/V2/V2.1+/Timelapse-Phase-2 are reserved for project release names — never reuse for prompt iterations, asset versions, or other versioning
metadata:
  type: feedback
---

Don't use `v1`, `v2`, `v2.1`, etc. as labels for anything that isn't a project release.

**Why:** CLAUDE.md "Versioning convention (locked S59)" reserves V1 / V2 / V2.1+ / Timelapse-Phase-2 as the *only* canonical names for shipping releases. Overloading the same letters/numbers for prompt iterations, asset baselines, smoke runs, etc. silently creates ambiguity in docs, Linear comments, and conversation — readers can't tell which "v2" is meant. User caught this S65 (called it "reuse/overload").

**How to apply:** When labeling prompt iterations, asset baselines, regen attempts, etc., use descriptive labels instead — `baseline`, `iteration_1`, `face_glow_fix`, dated suffixes (`bombale_2026-05-15.mp4`), or "first-pass / second-pass" prose. Reserve the letter `v` followed by a digit purely for project releases.
