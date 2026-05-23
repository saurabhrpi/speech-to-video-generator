---
name: higgsfield-kling3-mc-ui-only
description: Higgsfield's "Kling 3.0 Motion Control" is UI-only — no programmatic equivalent in their MCP, CLI, or API. ULTRA plan does NOT unlock it. Going direct with Kling is the only programmatic path for Kling 3.0 Motion Control.
metadata:
  type: reference
---

**Verified S72** (after installing Higgsfield CLI + skills + MCP, completing OAuth, and querying both MCP and CLI endpoints):

**Higgsfield's programmatic Kling surface (full server-side list):**
- `kling2_6` — accepts `start_image` x1 only (I2V)
- `kling3_0` — accepts `start_image`, `end_image` only (I2V with start/end frames)

**NO motion-control variant exists** — no `kling3_0_motion_control`, no `kling_motion_control`, nothing. The MCP `models_explore list type=video` returned 16 video models, `has_more: false`; the CLI's `higgsfield model list --json` returned the same 11 video models. Both confirm no MC endpoint.

**Plan tiers do NOT unlock additional models.** Both PLUS and ULTRA say "Access to all models" in `show_plans_and_credits`. Plans gate:
- Credits per month (PLUS=1000, ULTRA=3000)
- Parallel generation slots (PLUS=6 video, ULTRA=8 video)
- Rate (ULTRA gets 70% cheaper per credit)
- Some perks (Claude Opus 4.7 access, 7-day Unlimited promos)

They do **NOT** gate the endpoint surface — the model_id list is identical across plans.

**The web UI ships "Kling 3.0 Motion Control"** (3-30s driving video + character image, per user's screenshot in S72) but it's UI-only. Higgsfield most likely calls Kling's direct API server-side with their own auth and exposes the feature only through the browser experience.

**Going direct with Kling is the only programmatic path** for Kling 3.0 Motion Control today. See [[kling-v3-model-string-and-cost]] for the correct model_name string and cost data.

**How to apply:** When a provider advertises a feature in their UI, don't assume API parity — check both MCP/CLI/API surface AND plan-tier documentation before recommending a switch. Save time by going to the model `get` endpoint and reading the accepted media roles; if `video` isn't listed as a role, motion-control isn't programmatically available regardless of marketing copy.
