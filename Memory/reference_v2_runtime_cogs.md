---
name: reference_v2_runtime_cogs
description: Verified runtime COGS for a V2 motion-transfer gen — ~$1.50 for a 15s kling-v2.6-std video (Kling $1.05 + NBP $0.20 + Replit $0.25)
metadata:
  type: reference
---

**Verified S87 (2026-05-30) from the user's actual Kling account billing logs** — the real per-gen COGS for the shipping V2 Pipeline A motion-transfer path at the current runtime config (`kling-v2-6` + `std`):

| Component | Cost (15s gen) | Basis |
|---|---|---|
| Kling 2.6 **std** motion-control | **$1.05** | 7.5 Kling units × $0.14/unit, measured for a 15s output |
| NBP regen (Gemini 3 Pro image edit) | ~$0.20 | per-gen estimate |
| Replit / compute cushion | ~$0.25 | rough per-video allocation (not metered) |
| **Total** | **~$1.50** | for a **15s** v2.6-std gen |

**Kling-side per-second cost — CONFIRMED ~linear (S87):** Kling appears to bill on **whole seconds rounded up** at a flat per-second unit rate. Two std data points fit this exactly:

| Mode | Duration | Units | Billed sec (ceil) | Units/sec | $/sec |
|---|---|---|---|---|---|
| **v2.6-std** | 15.0s | 7.5 | 15 | 0.50 | $0.070 |
| **v2.6-std** | 10.67s | 5.5 | 11 | 0.50 | $0.070 |
| **v2.6-pro** | 14.5s | 12.0 | 15 | 0.80 | $0.112 |

- **std ≈ 0.50 units/sec = ~$0.07/sec** Kling-side. (Pure-linear-on-raw-seconds predicts 5.33u for 10.67s; observed 5.5u → the gap closes exactly if Kling ceils to whole seconds: 10.67→11→5.5u, 15→7.5u. 2-point fit — plausible, treat ceil-rounding as a hypothesis until a 3rd point.)
- **pro ≈ 0.80 units/sec = ~$0.112/sec** Kling-side (14.5s→ceil 15→12u×$0.14=**$1.68 Kling-only**). So **pro is 1.6× std** Kling-side. (Distinct from the v3≈2×v2.6 ratio in [[reference_kling_v3_model_string_and_cost]].) Runtime ships **std**; pro is used for catalog **preview** builds per [[project_kling_mode_split]].
- Good enough to drive **duration-based pricing (30 coins/sec)** — Kling-side COGS scales ~$0.07/sec on std.

**This SUPERSEDES the stale `docs/V2_motion_transfer_plan.md` figure of ~$1.12** (that was Kling **pro** mode, S58; runtime ships **std**). The std path is cheaper Kling-side per [[project_kling_mode_split]] but the NBP + Replit components push the *total* to ~$1.50.

**Pricing implication (S87 coins work):** at the proposed **30 coins/sec** with **100 coins = $1**, a 15s gen retails 450 coins = **$4.50** vs ~$1.50 COGS = **~3× COGS** (not the "2× COGS" rule in the plan doc — richer margin). Before Apple's 15% cut, net ~$3.83. The catalog's 45 templates run **7–16s** (bulk at 15s), so per-template price scales $2.10–$4.80.

Related: [[project_kling_mode_split]], [[reference_kling_runtime_config_commands]], [[reference_kling_v3_model_string_and_cost]] (v3 ≈ 2× v2.6 Kling-side), [[project_reliability_target_and_telemetry]].
