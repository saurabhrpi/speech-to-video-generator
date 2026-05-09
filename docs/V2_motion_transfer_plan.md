# V2 Motion-Transfer Implementation Plan

> **Versioning note:** V1 = the shipping Speech-to-Video app (live on App Store, Build #14 approved 2026-05-04). V2 = this release — adds motion-transfer as the new wedge product, restructures the home screen into a competitor-style template gallery, demotes S2V to a floating Create Video button.

**Created:** 2026-05-07 (S58)
**Updated:** 2026-05-07 (S59 — Q1/Q2/Q3/Q5 answered, launch subset locked, pipeline-class realization added)
**Status:** Q4 deferred; rest answered. Architecture updated: V2 ships **2 pipelines** (motion-transfer + scene-insertion), not 1. Launch subset locked at ~25 templates from 5 categories.
**Source material:** `docs/research/motion-transfer-providers-S57.md` (technical foundation — both outcomes locked on Kling). `docs/V2_template_catalog.md` (full theme list + per-category pipeline-class hypothesis).

---

## Product vision

The home screen replaces tab navigation entirely with a competitor-style template gallery:

- **Top 1/3 of home screen:** landscape-format "top trends" hero carousel — distinct visual treatment from the rows below.
- **Below the hero:** rows of template carousels, one row per theme. Each row = a horizontal scroll of templates.
- **No tabs.** Tab navigation removed.
- **Floating Create Video button:** triggers Speech-to-Video flow (the existing shipping product, demoted to secondary surface).
- **Top-right profile icon:** replaces the gear icon. Tap → user's gallery (their generated clips). Gallery has its own gear icon top-right → settings.

**Day-one scope:** ship BOTH motion-transfer outcomes together (Outcome 1 = user in template's scene; Outcome 2 = user in user's own scene). Outcome assignment is a template-level choice per `Memory/reference_motion_transfer_two_outcomes.md`.

**Templates:** dynamically populated from top-10 viral trends per theme on TikTok / Instagram. Themes TBD.

**Pipelines (locked S58):**
- **Outcome 2:** Kling 2.6 Motion Control, Pro mode, `image` orientation. Selfie + reference video → output. ~$1.12 COGS, ~5-6 min.
- **Outcome 1:** Nano Banana Pro Edit (v4 holistic-regen prompt) → Kling 2.6 Motion Control, Pro mode, `video` orientation. Selfie + reference video first frame → regen frame; regen frame + reference video → output. ~$1.16 COGS, ~7-8 min.

---

## V2 launch economics (S59-locked)

### Pricing model — pay-as-you-go credits, 2× COGS retail

**Decision (S59):** V2 abandons V1's tiered credit-pack pricing (50cr/$4.99, 120cr/$9.99, 250cr/$19.99 with bulk discount) in favor of **pay-as-you-go credits at a flat per-credit rate**.

**Pricing rule:** **retail = 2× COGS** for every gen pipeline. Yields ≥50% gross margin per gen *before* Apple's 15% Small Business cut; with cut, real net margin lands ~38-43%, which absorbs anon-free-tier giveaways.

**Implications for V2 launch:**

| Pipeline | COGS | 2× COGS retail | At 1cr = $0.10 (V1 unit) |
|---|---|---|---|
| Pipeline A — motion-transfer (Outcome 2) | $1.12 | $2.24 | ~22 cr/gen |
| Pipeline B — scene-insertion (Outcome 1) | $1.16 | $2.32 | ~23 cr/gen |
| V1 — S2V single-clip (legacy) | $0.50 | $1.00 | 10 cr/gen (unchanged) |

**Free tier:** anon starter-credit count TBD towards end of V2 build (S59 — explicit defer). Must cover at least 1 V2 gen if we want anon-tier wedge to work; otherwise free tier becomes a S2V-only experience and V2 conversion happens via paywall on first V2 attempt.

**ASC / RC operational impact:**
- Existing IAPs `pro_pack_50` / `pro_pack_120` / `pro_pack_250` need replacement with pay-as-you-go credit products. Likely 4-5 products at flat per-credit rate, satisfying Apple's minimum-price tiers (e.g., 10cr/$0.99, 50cr/$4.99, 100cr/$9.99, 250cr/$24.99 — all at $0.10/cr, no bulk discount).
- New RC offering ("v2_credits" or similar). Existing offering stays for V1 users until cutover.
- Backend `CREDIT_COSTS` gains entries for `("kling-motion", 10)` (Pipeline A) and `("kling-motion-scene-insert", 10)` (Pipeline B). Mobile `FALLBACK_COSTS` mirrors.

**Backend should NOT lock `CREDIT_COSTS` constants until per-pipeline credit costs are finalized — but the principle (2× COGS at $0.10/cr) is enough to scaffold registry schema.**

### Asset creation — AI-generated (Path 1)

**Decision (S59):** Reference assets for the ~25 launch templates are **AI-generated**. No stock licensing, no in-house filming, no freelance creators for V2 launch.

- **Dance reference videos (9 templates, category a)** — generated via T2V models (Veo / Kling / Sora). Per-provider commercial-license terms for derivative use must be verified before use.
- **Scene reference images (16 templates, categories f / l / i+k / r)** — generated via T2I models (Imagen / Midjourney / Nano Banana Pro). Same license-audit requirement.

**Quality gate:** generated assets must pass the "trend-recognizable" bar. Pipeline B's regenerated user-in-scene depends entirely on the source scene image — bad scene → bad output. Per-template QA before publishing is mandatory (already noted under Risk 2 / variance scaling).

**Pre-asset-work blockers:**
1. ✅ **License audit per provider — COMPLETE S59.** See `docs/V2_provider_license_audit.md` for full audit. Locked providers:
   - **T2V (dance reference videos): Veo 3.1** primary (Vertex AI, paid tier — indemnified, SynthID mandatory but invisible). **Hailuo 2.3** backup (already integrated; no indemnity, conservative prompts).
   - **T2I (scene reference images): Nano Banana Pro** primary (already in codebase as `google/nano-banana-pro-edit`; same Vertex stack as Veo, indemnified). **GPT Image 1.5** backup (post-DALL-E-3-retirement May 12 2026).
   - **Rejected:** Kling T2V (brand-display req breaks UX), Sora 2 (C2PA + opt-in IP restrictive), Pixverse (no upside), Seedance (active Hollywood litigation), FLUX (input-training clause + no indemnity).
2. **Asset generation pipeline / batch script** — extension of `scripts/kling_outcome1_spike.py` to drive bulk T2V/T2I via Veo + Nano Banana Pro and capture outputs to local `assets/templates/` for review before R2 upload. Track 1 backend work.

**Pre-launch unblocker (one — hard gate):**
- **Per-asset IP / likeness audit before R2 upload.** Manual review of every generated reference asset for incidental real-people likeness, recognizable IP (Disney/Marvel/anime/branded characters, copyrighted choreography), or trade-dress copying. Indemnity carve-outs depend on responsible-use compliance — this is the gate that keeps us covered.
- (Google written-confirmation request deprioritized S59. Self-interpretation memo lives in `V2_provider_license_audit.md` for future audit/legal trail.)

**Why not stock or in-house:** Path 2-4 are slower / costlier / both. Speed wins for V2 launch; quality acceptable as long as per-template QA gates publishing. Tier 2 quality issues (variance, identity drift) mitigated by `published_status` flag, not by asset-source choice.

---

## Load-bearing risks

### Risk 1 — Legal / licensing on viral TikTok/IG content (RESOLVED S59 — discovery-only)

Original framing: hosting actual viral TikTok/IG videos as our templates exposed us to TOS violations, DMCA takedowns, and Apple App Review scrutiny.

**Resolution (S59):** discovery-only model. Paid trend-data feeds tell us *what's* trending; we never host original creator videos. Reference assets are AI-generated (S59 asset-creation decision). Naming caveat carried over: dance-trend names that share song titles need legal pass before launch — see `V2_template_catalog.md` §4.

Residual risk: AI-generated reference quality must capture the trend recognizably without copying any specific creator's choreography frame-for-frame. Per-template QA gates publishing.

### Risk 2 — Variance scaling

The v4 motion-transfer pipeline is currently verified on ONE input pair (one selfie × one dance video). Shipping with 10 trends × N themes means hundreds of (template × user-photo) combinations possible. If even 20% produce paste-in / wrong-identity outputs, that's a quality crisis at scale.

Mitigations needed:
- **Per-template QA before publishing:** test each template with 3-5 representative user photos before flipping it on.
- **Quality-flag mechanism:** server-controlled `published_status` so we can fast-disable bad templates without an app update.
- **User-reported quality feedback:** surface a "this generation looks wrong" path so we catch templates that pass our QA but fail in the wild.

Affects template registry schema and team CMS workflow (someone has to QA new templates).

### Risk 3 — Apple App Store review surface area (S59 — Tier 2)

V2 introduces user-uploaded photos + AI-regenerated person imagery + motion-transfer onto user faces. Materially higher review-rejection surface than V1's text/voice → AI clip flow.

**Specific concerns:**
- **Privacy / 4.8 / 5.1.1:** Privacy policy must explicitly cover photo upload, on-device handling, retention, deletion. Current V1 policy is text/voice only — needs rewrite.
- **Deepfake / 4.3 / 1.1.6:** Generating realistic video of a recognizable person (the user themselves, or any photo they upload) raises deepfake-content review flags. Apple has approved similar competitor apps (Higgsfield, Pollodance, etc.) so precedent exists, but rejections happen.
- **Derivative content / 5.2.4:** Trend-recognizable templates risk "encourages copying real creators" framing. AI-generated reference assets help; per-template name + thumbnail review still required.
- **Consent flow:** if user uploads a photo of someone *other than themselves*, we need an explicit "I confirm this person consented" checkbox or similar UX gate. Several competitors do this; not yet wired into our flow.

**Mitigations to plan in:** privacy policy rewrite, consent checkbox in template-detail screen, server-side audit log for uploaded user photos, fast-disable mechanism for any template that gets review-flagged post-launch.

### Risk 4 — Latency UX at 7-8 minutes (S59 — Tier 2)

V1 (S2V) is ~30-60s — tap-and-wait is acceptable. V2 Pipeline B is **7-8 minutes**; Pipeline A is **5-6 minutes**. Both are at or beyond the threshold where users will background the app, switch tasks, or just leave.

**Implications:**
- First-gen experience is brutal. New users wait 5-8 min for the magic moment that proves the product. High abandonment risk.
- Job state must survive app backgrounding + cold start. Existing job manager is in-memory and ephemeral; survives a 7-min background fine on most iOS but breaks if backend redeploys mid-job.
- Push notifications become essentially mandatory for V2 (V1 carryover from `ToDo.md` #19). User taps Generate → backgrounds app → push fires when ready.
- In-app distraction loop helps too — preview other templates while waiting, browse gallery, see other users' outputs. Adds product surface but reduces abandonment.

**Mitigations to plan in:** push-notification infra (APNs via Firebase Cloud Messaging since auth is already on Firebase), generation-progress phases mapped to user-facing copy ("rendering scene", "blending you in", "finishing touches"), in-app browse-while-waiting affordance.

### Risk 5 — Variance failure rate at production load (S59 — Tier 2; overlap with Risk 2)

The v4 holistic-regen pipeline is verified on **one** (selfie × dance-video) pair. We don't know the production failure rate. Different selfies (full-body, women, glasses, low-light, kids), different reference videos (non-dance, different framing), different scene images (dense vs sparse, indoor vs outdoor) all exercise edge cases we haven't tested.

If the launch failure rate is even ~15-20%, paid users will get a paste-in / wrong-identity / mangled output regularly enough to crush retention.

**Mitigations to plan in:** variance-testing harness extended to batch-mode (Track 3); per-template QA on 3-5 representative photos before `published_status: true`; user-reported "this looks wrong" path that auto-credits the gen and flags the template; quality-flag dashboard to fast-disable templates whose live-failure rate exceeds threshold.

(Risk 2 is the registry/CMS-workflow flavor of this; Risk 5 is the customer-experience flavor. Same underlying issue.)

---

## Clarifying questions — answered S59

1. **Trend ingestion strategy. ✅ ANSWERED — discovery-only.** Paid trend-data feed identifies *what's* trending; we do NOT host actual viral videos. We recreate templates ourselves (AI-gen / our own footage / licensed stock) that capture the trend's vibe. Solves the legal-risk problem at the cost of asset-creation work per template.
2. **Theme list. ✅ ANSWERED.** Full list captured in `docs/V2_template_catalog.md` — 24 categories, ~150 templates total. (j) and (p) explicitly deferred per user direction. Launch subset (S59-locked): see "V2 launch subset" section below.
3. **"Top trends" hero carousel content. ✅ ANSWERED — recreated approximations.** Top 10 hottest trending TikTok/IG videos, but rendered as our own recreations (same legal model as Q1). Distinct from the row-templates below (separate curated set).
4. **Outcome assignment per template. ⏸ DEFERRED** — decide once we hit per-template build-out.
5. **Template asset hosting. ✅ ANSWERED — Cloudflare R2.** $0.015/GB storage, $0 egress. Templates get watched repeatedly, so egress dominates everywhere else; R2 wins.

## V2 launch subset (S59-locked)

**~25 templates across 5 categories, 2 pipelines.** Validates both the motion-transfer wedge and the home-screen carousel UX across pipeline types. Other categories (b, c, d, e, g, h, m, n, o, q, s, t, u, v, w, x) shift to V2.1+. (j) and (p) deferred end of implementation.

| Category | Pipeline | Take | Notes |
|---|---|---|---|
| (a) Viral Dances | Motion-transfer (Kling Motion Control, Outcome 2) | All 9 | Pure wedge — proves the verified S58 spike scales. |
| (f) Trends | Scene-insertion (Nano Banana Edit → I2V) | 5 of 18 | Specific picks TBD. |
| (l) Birthday Photoshoot | Scene-insertion | 4 of 6 | Specific picks TBD. |
| (i) Awards Night + (k) Winter Olympics | Scene-insertion | 4 (2 + 2) | Specific picks TBD. |
| (r) Flying | Scene-insertion | 3 of 8 | Specific picks TBD. |

## Pipeline-class realization (S59)

The V2 catalog spans **multiple pipeline classes**, not just motion-transfer. V2 launch subset uses 2 of them:

- **Pipeline A — Motion-transfer (Outcome 2).** Kling Motion Control 2.6 Pro, `image` orientation. Selfie + reference dance video → output. Verified end-to-end S58. ~$1.12 COGS, ~5-6 min.
- **Pipeline B — Scene-insertion (Outcome 1).** Nano Banana Pro Edit (v4 holistic-regen prompt) → I2V. Selfie + scene reference → regenerated user-in-scene image → I2V clip. **V2 launch locks Kling 2.6 Motion Control `video` mode** (S58 verified) — same model as Pipeline A. ~$1.16 total COGS, ~7-8 min. I2V cost-optimization spike deferred — see "Deferred spikes" below.

Backend implication: `generate_template_video()` is a dispatch layer that routes by `template.pipeline_class` to one of these handlers. Per-template registry needs both `pipeline` and `outcome` fields (not just one).

V2.1+ pipelines we know are coming but are NOT in launch subset: I2I-only (caricatures), style-transformation (animal-transform / monochrome / earthly-effects), reverse-playback I2V (metamorphosis).

---

## Implementation work breakdown

### Track 1 — Backend (can start on items not gated by clarifying questions)

| Item | Gated by | Effort |
|---|---|---|
| `VideoService.generate_template_video()` dispatch by `pipeline_class` | None | small |
| Pipeline A handler — motion-transfer (Outcome 2, Kling Motion Control) | None — verified S58 | small (wraps existing client) |
| Pipeline B handler — scene-insertion (Outcome 1, Nano Banana Edit → I2V) | I2V model choice spike | small + spike |
| First-frame extraction utility (ffmpeg via `imageio-ffmpeg`) | None | small |
| `POST /api/generate/template-video` endpoint | None | small |
| Template registry schema design (incl. `pipeline_class`, `outcome`, `published_status`, asset URLs) | None (populate later) | small |
| Variance-testing harness (extend `kling_outcome1_spike.py` for batch + take input URLs as args) | None | small |
| ~~I2V-model spike for Pipeline B~~ — DEFERRED to post-V2-launch (see "Deferred spikes") | — | — |
| Pricing entries in `CREDIT_COSTS` (per-template credit cost) | Pricing decision | trivial |
| Cloudflare R2 wiring — bucket, signed-URL flow, template asset upload | None (Q5 ✅) | medium |
| Discovery-only trend ingestion — paid trend-data integration + manual recreation flow | Trend-data provider choice | LARGE — V2.1, NOT V2 launch (V2 launch uses hand-curated subset) |

### Track 2 — Mobile (depends on Track 1 API + UX directives)

| Item | Gated by | Effort |
|---|---|---|
| Restructure `mobile/app/` — remove tab nav, new home screen entry | None | medium |
| Home screen — hero carousel + theme rows | Q3 (hero content), Q2 (themes) | medium |
| Template detail screen — preview + photo picker + Generate | Track 1 API stable | medium |
| Floating Create Video button → S2V flow integration | None | small |
| Top-right profile icon → gallery → gear → settings nav | None | small |
| Job polling + clip in user's gallery | Reuse existing `gallery-store` | small |
| Latency UX (5-8 min progress phases, possibly push notifications) | None for V2 phases; push needs new infra | medium |

### Track 3 — Variance testing (parallel; gates broad release, not implementation start)

| Item | Notes |
|---|---|
| Test v4 pipeline on more inputs | Different selfies (full-body, women, glasses, low-light), different reference videos (non-dance, different framing). Use spike script. |
| Identify failure modes | Frequency of paste-in / wrong-identity / framing fails. Sets expectations for retry-UI need. |
| Establish per-template QA criteria | Quality bar checklist before flipping `published_status` to true. |

### Track 4 — Content + product (user's domain)

| Item | Notes |
|---|---|
| Reference video library | Sourcing path locked in Q1. Need 1-3 templates per theme to launch. |
| Pricing strategy decision | Same retail price for both outcomes vs tier? With Outcome 1 at $1.16 COGS and Outcome 2 at $1.12, plus Apple's 15% cut, ~12-18 credits per gen feels reasonable. |
| Theme curation rules | What makes a "trend" template-worthy? |
| Quality bar criteria | When is a template good enough to publish? |

---

## Recommended starting sequence

1. **User answers the 5 clarifying questions** above.
2. **Backend (parallel with #1):** start on Track 1 items not gated by questions — orchestration, first-frame utility, endpoint, schema, variance-testing harness.
3. **End of Track 1 milestone:** `curl POST /api/generate/template-video` with hardcoded test templates produces a finished clip via the deployed backend, both outcomes working.
4. **Mobile restructure (Track 2):** UI overhaul. End milestone: real device install with end-to-end happy path through the new home screen.
5. **Variance testing (Track 3) in parallel** with Track 2 — user spikes input variance, I keep building.
6. **TestFlight build for internal validation** before shipping to App Store.
7. **App Store update** with motion-transfer feature.

---

## Deferred spikes (post-V2-launch)

### Pipeline B I2V cost-optimization spike

**Status:** Deferred S59. V2 launch uses Kling 2.6 Motion Control `video` mode for Pipeline B's I2V step ($1.12 of the $1.16 COGS).

**Why this exists:** Kling Motion Control is designed for character-motion-transfer. Pipeline B's I2V step doesn't need motion transfer — it just needs to bring a regenerated still into motion. Plain I2V models should work and are 4-5x cheaper.

**Spike scope when revisited:**

| Model | Estimated cost / 10s | Rationale |
|---|---|---|
| Hailuo I2V (`minimax/hailuo-02`) | ~$0.25 | Cheapest path. If quality holds → Pipeline B COGS drops $1.16 → ~$0.30. |
| Kling 2.1 Standard I2V (NOT Motion Control) | ~$0.50–0.80 | Mid-tier fallback. |
| Kling 2.6 Motion Control video-mode (current) | $1.12 | Reference quality bar. |

**Pre-spike inputs needed:** 1 v4 Nano Banana regenerated user-in-scene image (reuse S58 spike output if locatable, else regenerate $0.04). Run all 3 endpoints.

**Decision criterion:** identity preservation + scene coherence + motion realism — head-to-head against the S58 baseline.

**Cost to run:** ~$2-4 API spend, 30-45 min.

**Why deferred:** Pricing/margin questions are a bigger elephant; cost-optimization on Pipeline B's I2V step is a margin lever, not a launch blocker. Revisit when V2 retail pricing forces COGS reduction.

---

## App rename (S59 — deferred to end of V2 build)

**Decision:** rename the app at the END of V2 implementation, not now. **Scope:** display name only — App Store display name + `mobile/app.json` `name` field + UI brand strings. Slug (`speech-to-video`), scheme (`speechtovideo`), bundle ID, domain (`speech-2-video.ai`), repo name, Firebase project, RC project all stay as-is. Lowest-disruption rename.

**Rationale:** "Speech to Video" no longer reflects the product (V2 demotes S2V to a floating button; template-driven motion-transfer + scene-insertion become the core surface). New name to be picked once V2 UX is mostly built so the name lands against actual product identity, not anticipated identity.

---

## Open product decisions blocking final scope

- Q1-Q5 above (immediate).
- Pricing tier for Outcome 1 vs Outcome 2 (post backend, pre-launch).
- Push-notification infrastructure decision (post-launch acceptable; longest gens are 7-8 min).
- "What if a template QA-fails?" — kill / iterate / replace policy.

---

## Status snapshot

- **Vision:** locked Session 58.
- **Both pipelines:** technically locked, single test verified for Outcome 1.
- **Single-provider architecture:** Kling for both outcomes; Nano Banana for Outcome-1 pre-step.
- **Pollo `mix`:** dropped from V2.
- **Outstanding before code:** 5 clarifying questions + legal-risk decision on TikTok/IG sourcing.
