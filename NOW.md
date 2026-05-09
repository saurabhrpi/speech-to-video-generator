# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 59 — 2026-05-07 / 2026-05-08 — branch `v2`

**Status:** V2 strategic-decision phase mostly resolved. All 5 clarifying questions answered (Q4 deferred late). Both elephants tackled (pricing model + asset-creation path). License audit complete with locked providers. Versioning convention unified. Linear MCP registered (activates next session). Ready for tactical execution: template picks → backend Track 1 kickoff.

## What happened this session

- **Branch renamed** `home-screen-redesign` → `v2` (origin pushed, old remote deleted, NOW.md updated).
- **Q1, Q3, Q5 of V2 plan answered.**
  - Q1 (CRITICAL/legal): **discovery-only** trend ingestion. Paid trend-data feeds tell us what's hot; we recreate templates ourselves (AI-generated). Solves the TikTok/IG hosting legal risk; introduces asset-creation work as the long pole.
  - Q3: **recreated approximations** for hero carousel — top-10 hottest TikTok/IG videos rendered via our own AI-gen, not actual viral videos.
  - Q5: **Cloudflare R2** for template asset hosting ($0 egress).
- **Theme list captured.** User shared 24 categories / ~150 templates. Saved verbatim at `docs/V2_template_catalog.md`. (j) Product Showcase + (p) Text to video explicitly **deferred** to end of V2 build.
- **Pipeline-class realization.** V2 catalog spans multiple pipeline classes, not just motion-transfer. V2 launch ships **2 pipelines**:
  - Pipeline A — motion-transfer (Outcome 2, Kling 2.6 Motion Control image mode)
  - Pipeline B — scene-insertion (Outcome 1, Nano Banana Pro Edit → Kling Motion Control video mode)
  Backend implication: `generate_template_video()` is a dispatch layer routing by `template.pipeline_class`, not a single handler.
- **V2 launch subset locked.** "Dances + Scenes (~25)": 9 from (a) Viral Dances + 5 from (f) Trends + 4 from (l) Birthday + 4 from (i+k) Awards/Olympics + 3 from (r) Flying. 16 specific picks within scene-insertion pools still TBD. Other categories shift to V2.1+.
- **Versioning convention unified across all docs.** V1 = shipping S2V app. V2 = next release (motion-transfer + home redesign). V2.1+ = post-V2-launch phases. **Timelapse-Phase-2** = the (paused) renovation pipeline (renamed from "Timelapse V2" to remove collision with project-release V2). CLAUDE.md gained a new Versioning convention block at the top; all V2 docs updated for consistency.
- **Pipeline B I2V cost-optimization spike deferred.** V2 launch uses Kling Motion Control video mode for both pipelines ($1.16 COGS for Pipeline B). Cheap-I2V spike (Hailuo / Kling 2.1 standard) captured at end of plan doc as post-launch margin lever, not a launch blocker.
- **Elephants tackled.**
  - **#1 Pricing math.** S2V economics ($0.50 COGS, 10cr/$1) don't survive V2's $1.12-1.16 COGS at current credit-pack prices (would be net-negative after Apple's 15%). **Decision: pay-as-you-go credits at flat $0.10/cr, retail = 2× COGS** (≈22-23cr per V2 gen). No more bulk-discount packs. Existing IAPs (`pro_pack_50/120/250`) replaced with flat-rate products. Free-tier credit count TBD-end.
  - **#2 Asset creation.** **Decision: AI-generated (Path 1)** — T2V for dance refs, T2I for scene refs. Faster + cheaper than stock licensing or in-house filming.
- **Tier 2 risks documented as Risks 3-5 in plan doc.**
  - Risk 3 — Apple App Store review surface (privacy/4.8/4.3, deepfake concerns, consent UX).
  - Risk 4 — Latency UX at 7-8 min (push notifications + in-app distraction loop needed).
  - Risk 5 — Variance failure rate at production load (per-template QA before publish, user-flag path, dashboard).
- **App rename deferred to end-of-build.** Scope = display name only (App Store name + `mobile/app.json` `name` + UI brand strings). Slug, scheme, bundle ID, domain, repo, Firebase, RC all stay. Naming brainstorm at end of build, after V2 UX is real.
- **License audit run + complete** (subagent did the research). Saved at `docs/V2_provider_license_audit.md`.
  - **T2V locked: Veo 3.1 primary, Hailuo 2.3 backup.** Veo is the only T2V provider in the audit offering IP indemnification (Google Generated Output Indemnity). Mandatory SynthID watermark — invisible.
  - **T2I locked: Nano Banana Pro primary, GPT Image 1.5 backup.** Same Vertex AI license stack as Veo. DALL-E 3 retires from API May 12 2026 — migration to GPT Image 1.5 needed.
  - **Rejected:** Kling T2V (brand-display req breaks UX), Sora 2 (C2PA + opt-in IP restrictive), Pixverse (no upside), Seedance (active Hollywood Disney/Netflix/Paramount C&D Feb 2026), FLUX (input-training clause + no indemnity).
- **Pre-launch unblockers reduced 2 → 1.** Only hard gate remaining: per-asset IP/likeness audit before R2 upload. Google written-confirmation request deprioritized; self-interpretation memo added to license audit doc as evidentiary trail for future legal/audit.
- **Linear MCP server registered** via `claude mcp add --transport http linear-server https://mcp.linear.app/mcp`. Tools activate on next session start.

## Next step — Session 60 (on resume)

1. **Restart Claude Code session** to activate Linear MCP tools. First Linear tool call triggers OAuth flow.
2. **Organize V2 work into Linear:**
   - Pick a team/project (existing, or create new "V2" project).
   - Decide structure (Project + Cycle + Issues, or Issues with labels).
   - Import sources: V2 launch subset templates (25 work items), open questions list below, ToDo.md carryover, launch checklist (per-asset audit, pricing IAP setup, Apple consent UX, push notif infra, etc.).
3. **Specific template picks (16 from scene-insertion pools).** I propose with reasoning per template; user OKs/overrides. Pools: 5 from (f) Trends, 4 from (l) Birthday, 4 from (i+k) Awards+Olympics, 3 from (r) Flying.
4. **Backend Track 1 kickoff** (parallel-able with #3):
   - Template registry schema (`pipeline_class`, `outcome`, `published_status`, asset URLs, title, description, theme).
   - Vertex AI client scaffolding (Veo + Nano Banana Pro — already partially exist via paused Timelapse path).
   - Cloudflare R2 wiring (bucket, signed-URL flow, asset upload).
   - First-frame extraction utility (ffmpeg via `imageio-ffmpeg`).
   - `generate_template_video()` dispatch shell + `POST /api/generate/template-video` endpoint scaffolding.
   - Variance-testing harness (extend `scripts/kling_outcome1_spike.py`).
5. **Asset generation pipeline / batch script** — once template picks are locked, drive bulk Veo/Nano Banana generation, capture to local `assets/templates/`, manual per-asset IP/likeness audit, then R2 upload + `published_status: true`.

## Branch state at close

- On `v2` (S59 rename from `home-screen-redesign`). HEAD `3af5d6c` (last push S58: "Adding docs, memories and test scripts").
- **Working tree dirty (S59 strategic work uncommitted, intentional — to be committed next session):**
  - `M NOW.md` (this file)
  - `M docs/V2_motion_transfer_plan.md` (S59 updates: Q1/Q3/Q5 answered, V2 launch subset locked, pipeline-class realization, V2 launch economics section, asset creation path, Tier 2 risks, app rename, deferred spikes, license audit results)
  - `?? docs/V2_template_catalog.md` (NEW S59 — full theme list, pipeline-class hypothesis, V2 launch subset, deferral notes)
  - `?? docs/V2_provider_license_audit.md` (NEW S59 — full provider audit, locked recommendations, vendor indemnity self-interpretation memo)
- `main` at `6aa2c2b`. `hotfix-build14` at `a432301`.

## Open questions

### S59 new — V2 STRATEGIC

- **(S59 new — TACTICAL)** Specific 16 template picks from scene-insertion pools (5 trends + 4 birthday + 4 awards/olympics + 3 flying). Gates asset generation.
- **(S59 new — TACTICAL)** V2 anon free-tier credit count. Current 10cr starter doesn't cover one V2 gen (~22-23cr). Decisions: bump to 25cr, separate "first V2 gen free" grant, or keep 10cr and force paywall on first V2 attempt? TBD-end.
- **(S59 new — TACTICAL)** Final retail credit cost per pipeline. 22cr (Pipeline A, $2.20 retail) vs 23cr (Pipeline B, $2.30 retail), or unify at one number for UX simplicity? Lock before Track 1 backend `CREDIT_COSTS` pass.
- **(S59 new — TACTICAL)** New IAP product set creation in ASC for pay-as-you-go credits at flat $0.10/cr (10/50/100/250cr products), and matching RC offering.
- **(S59 new — DEFERRED)** App rename. End-of-V2-build, display-name only.
- **(S59 new — DEFERRED)** (j) Product Showcase + (p) Text to video disposition (defer to end).
- **(S59 new — DEFERRED)** Pipeline B I2V cost-optimization spike (Hailuo I2V vs Kling 2.1 standard). Post-launch margin lever.
- **(S59 new — TIER 2)** Apple App Store review prep: privacy policy rewrite for photo upload + retention; user-photo consent UX; deepfake/4.3 review strategy; per-template thumbnail review.
- **(S59 new — TIER 2)** Latency UX at 7-8 min: push notification infra (FCM via Firebase since auth is already there); in-app browse-while-waiting affordance; generation-progress phase copy.
- **(S59 new — TIER 2)** Variance testing at scale before launch: batch test v4 pipeline across (template × selfie) combos; per-template QA gate at 3-5 photos before `published_status: true`; user-reported quality flag path; quality-flag dashboard.
- **(S59 new — LINEAR)** Linear workspace structure: existing project vs new "V2" project; what to import from `ToDo.md` + `NOW.md` open questions; Project/Cycle/Issues vs Issues-with-labels.

### S58 carryover — STILL OPEN

- **(S58)** First organic Apple IAP purchase. Sandbox/TestFlight validated; production grant path untested. Watch RC dashboard + backend logs on first organic transaction.
- **(S55 / de-prioritized)** Viggle key still pending. Kling delivers both V2 outcomes; no urgency.
- **(S53)** Dad's Apple Developer enrollment retry from home WiFi.
- **(S53)** M365/Entra tenant decision (ToDo #26).
- **(S48 follow-up B)** UX hole: home button shows action label only, balance only in Settings. V2 home-screen redesign may obviate or change this.
- **(ToDo #19, S49+S48)** CustomerInfo listener for offline-replay + RC ingestion-lag.
- **(ToDo #27, S54)** Verify concurrent-submit credit gate post-deploy.
- **(Yellow #10)** Backend Apple precheck + clip-merge — `/api/auth/apple/precheck` + `/api/clips/merge` existence not yet verified in `server.py`.
- **(S43-era, future trigger)** RC `default` offering "Current" implicit — flag if a second offering arrives and `getOfferings().current` returns null.
