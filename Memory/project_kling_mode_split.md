---
name: kling-mode-split
description: Preview build vs user-gen runtime use different Kling settings. Preview chain scripts hardcode pro+v2.6 (catalog quality). Runtime is now config-driven per AIV-101 (Firestore + per-template override), baseline std+v2.6. Don't conflate the two paths — they're separate by design.
metadata:
  type: project
---

**The split:**

| Path | Code site | Settings | Why |
|---|---|---|---|
| Preview chain scripts | `scripts/test_*_chain.py` (e.g. `test_no_batidao_chain.py`) | **Hardcoded** `KLING_MODE="pro"`, `KLING_MODEL_NAME="kling-v2-6"` | Catalog-quality home-tile preview (1300-1500px) — shown to users before they pay |
| Runtime user gens | `video_service.py` Pipeline A + B call sites (~line 990, ~line 1154) | **Config-driven** via `VideoService._resolve_kling_settings` (AIV-101). Baseline `std + v2.6`. | Per-template override → global Firestore → hardcoded fallback. Flip with `scripts/set_kling_runtime.py` (global) or `scripts/set_template_kling_override.py` (one template). No redeploy. |

**Why the split exists:**
- S73 No Batidão initial run used std + v2.6 → 960×960 @ 3.3 Mbps preview. Visibly lower-res than the rest of the published catalog (1300-1500px @ 17-30 Mbps from pro-mode runs). Re-ran with pro to bring it in line. Sunk ~$1.50 Kling-side on the discarded std preview — the lesson is **always start template previews with pro**.
- Runtime can stay on std (baseline) because (a) user is generating against their own selfie they already know — no comparison anchor against a higher-res reference; (b) 720p is sharp on the iPhone screens we ship to; (c) Kling-side cost is ~$0.50/gen vs pro's ~$1.
- v2.6 baseline over v3: v3 costs ~2× v2.6 at the Kling-API level (S72 measured). S74's v3 trial showed it improved clean-driver templates (Bad) but regressed dirty-driver templates (Smooth Criminal, where burnt-in TikTok UI overlays leaked into the output). Per-template overrides exist exactly so we can mix-and-match without trading one regression for another.

**How to apply:**
- **New template preview chain script:** copy `scripts/test_no_batidao_chain.py` shape — `KLING_MODE = "pro"`, `KLING_MODEL_NAME = "kling-v2-6"`, `KLING_CHARACTER_ORIENTATION = "video"` (15s) or `"image"` (10s) depending on driving length. **Preview scripts stay hardcoded** — they're spike scripts for the per-template build, not runtime.
- **Touching runtime Kling MC call sites:** do NOT re-introduce hardcoded `mode=` or `model_name=` kwargs. The resolver owns them now. If you want to change runtime defaults, edit `_DEFAULTS` in `utils/runtime_config.py` (last-resort fallback only) or flip the global via the CLI (normal operation).
- **Per-template tuning:** if a template needs different settings than global, use `scripts/set_template_kling_override.py`. Set once, sticks across global flips. Don't fork the code path.
- **UX risk to monitor:** users see pro-mode preview, get std-mode output by default. So far untested in production; if user-feedback flags "looks worse than the preview," flip global to `v2-6-pro` (one CLI command, no redeploy).

**Future considerations:**
- Bump preview chain scripts to `kling-v3` for facial consistency (S72 spike, ~2× cost). Worth it ONLY if visibly better than v2.6+pro at home-tile scale on iPhone. Runtime stays config-driven regardless.
- A/B per-template: pin individual templates to `v3` via override if their content benefits, leave global on `v2.6` for cost.

See related: [[kling-runtime-config-commands]] (the CLI surface), [[kling-v3-model-string-and-cost]] (cost math), [[kling-mc-aspect-inherits-nbp]] (aspect interactions), [[template-preview-crf]] (preview encoding).
