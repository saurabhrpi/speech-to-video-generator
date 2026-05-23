---
name: kling-mode-split
description: S73-locked design — preview chain scripts use Kling pro mode for catalog-quality home-tile previews; runtime (user paid gens) uses std mode to halve Kling-side cost. Both pinned to v2.6, NOT v3. Pipeline B kept consistent with Pipeline A even though no Pipeline B templates ship today.
metadata:
  type: project
---

**The split (S73-locked):**

| Path | Code site | mode | model_name | Why |
|---|---|---|---|---|
| Preview chain scripts | `scripts/test_*_chain.py` (e.g. `test_no_batidao_chain.py`, `test_thriller_chain.py`) | `pro` | `kling-v2-6` | Catalog-quality home-tile preview (1300-1500px) — these get shown to users before they pay |
| Runtime user gens | `video_service.py` (Pipeline A ~line 969, Pipeline B ~line 1126) | `std` | `kling-v2-6` | User-paid gen — std (720p, ~960px) is still sharp on phone and halves Kling-side cost (~$0.50 vs pro's ~$1) |

**Why:**
- S73 No Batidão initial run used std + v2.6 → 960×960 @ 3.3 Mbps preview. Visibly lower-res than the rest of the published catalog (Bombale, Gangsta, Baby Dance, Smooth Criminal etc. all 1300-1500px @ 17-30 Mbps from pro-mode runs). Re-ran with pro to bring it in line at 1440×1440 @ 14.6 Mbps. Sunk ~$1.50 Kling-side on the discarded std preview — the lesson is **always start template previews with pro**.
- Runtime can stay on std because (a) user is generating against their own selfie they already know, no comparison anchor against a higher-res reference; (b) 720p is sharp on the iPhone screens we ship to.
- v2.6 over v3 across the board: v3 costs ~2× v2.6 at the Kling-API level (S72 measured). v3's facial-consistency win has not been A/B-tested against real-user data; until it has, the cheaper model wins by default. Client default in `kling_motion_client.py` stays `kling-v3` for now — the load-bearing override is at the call site (runtime explicit; chain scripts explicit).

**How to apply:**
- **New template preview chain script:** copy `scripts/test_no_batidao_chain.py` shape — `KLING_MODE = "pro"`, `KLING_MODEL_NAME = "kling-v2-6"`, `KLING_CHARACTER_ORIENTATION = "video"` (15s) or `"image"` (10s) depending on driving length.
- **Touching runtime Kling MC call sites:** keep `mode="std"` + `model_name="kling-v2-6"` explicit. Never rely on client defaults — they currently point at the more-expensive `kling-v3` + `pro`.
- **UX risk to monitor:** users see pro-mode preview, get std-mode output. So far untested in production; if user-feedback flags "looks worse than the preview," reconsider the split (move runtime to pro, or downgrade preview to match).

**Future consideration (S73-flagged):** preview templates could be bumped to `kling-v3` (better facial consistency per S72 spike) while runtime stays at `kling-v2-6`. Same split logic as mode (pro/std) — invest in catalog-quality previews, keep runtime cheap. Worth the cost (~$2 vs ~$1 Kling-side per preview) ONLY if v3's facial-consistency lift is visibly better than v2.6 in the regen-character-into-dance use case. Spike before adopting: do one template with v3+pro+video+15s, A/B against the v2.6+pro+video+15s version at home-tile scale on iPhone. If imperceptible, stay on v2.6. If clearly better, flip preview chain scripts to v3 (single-line change at `KLING_MODEL_NAME`) and leave the runtime call sites in `video_service.py` untouched.

See related: [[kling-v3-model-string-and-cost]], [[kling-mc-aspect-inherits-nbp]], [[template-preview-crf]].
