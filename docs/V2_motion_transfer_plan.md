# V2 Motion-Transfer Implementation Plan

> **Versioning note:** V1 = the shipping Speech-to-Video app (live on App Store, Build #14 approved 2026-05-04). V2 = this release — adds motion-transfer as the new wedge product, restructures the home screen into a competitor-style template gallery, demotes S2V to a floating Create Video button.

**Created:** 2026-05-07 (S58)
**Status:** Vision agreed. Two load-bearing risks flagged. 5 clarifying questions to user. Backend track ready to start once questions resolve.
**Source material:** `docs/research/motion-transfer-providers-S57.md` (technical foundation — both outcomes locked on Kling).

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

## Load-bearing risks

### Risk 1 — Legal / licensing on viral TikTok/IG content (CRITICAL)

Using actual viral TikTok/Instagram videos as our templates means:
- The original creators own their videos. TikTok/IG's TOS restrict downstream use.
- Apple App Review will likely flag this if we ship reference videos that look like recognizable viral content without licenses.
- DMCA takedowns from individual creators are a real ongoing cost.
- Competitor paths: (a) license through a trend-data provider, (b) recreate viral choreography with their own performers, (c) use AI-generated approximations of viral motion.

**This is the single biggest risk in the plan.** Could kill the wedge before launch if we get it wrong. Needs a deliberate decision before we build template ingestion.

### Risk 2 — Variance scaling

The v4 motion-transfer pipeline is currently verified on ONE input pair (one selfie × one dance video). Shipping with 10 trends × N themes means hundreds of (template × user-photo) combinations possible. If even 20% produce paste-in / wrong-identity outputs, that's a quality crisis at scale.

Mitigations needed:
- **Per-template QA before publishing:** test each template with 3-5 representative user photos before flipping it on.
- **Quality-flag mechanism:** server-controlled `published_status` so we can fast-disable bad templates without an app update.
- **User-reported quality feedback:** surface a "this generation looks wrong" path so we catch templates that pass our QA but fail in the wild.

Affects template registry schema and team CMS workflow (someone has to QA new templates).

---

## Clarifying questions (gate Track 1 startup)

1. **Trend ingestion strategy.** How are trends "pulled"? Options: manual curation by user (download from TikTok), API from a trend-data provider, AI-generated approximations, or a mix. Different answers = very different infrastructure + legal posture.
2. **Theme list.** Which themes for V2? E.g. Dance / Comedy / Transformation / Sports / Couples / Reactions. Affects row count + product organization.
3. **"Top trends" hero carousel content.** Is this the SAME templates as below (just different display), or distinct curated content (editorial picks, featured user outputs, showcase reels)?
4. **Outcome assignment per template.** Outcome is template-level. Who decides per trend — user, AI heuristic, manual curator? Need a process for setting `outcome: 1 | 2` per template.
5. **Template asset hosting.** With many videos + thumbnails + first-frames, static-from-Replit no longer scales. Decision needed: S3 / Cloudinary / Bunny CDN / other. Affects backend wiring.

---

## Implementation work breakdown

### Track 1 — Backend (can start on items not gated by clarifying questions)

| Item | Gated by | Effort |
|---|---|---|
| `VideoService.generate_template_video()` orchestration logic | None | small |
| First-frame extraction utility (ffmpeg via `imageio-ffmpeg`) | None | small |
| `POST /api/generate/template-video` endpoint | None | small |
| Template registry schema design | None (populate later) | small |
| Variance-testing harness (extend `kling_outcome1_spike.py` to take input URLs as args) | None | small |
| Pricing entries in `CREDIT_COSTS` (per-template credit cost) | Q3 (retail price decision) | trivial |
| Static template asset hosting wiring | Q5 (CDN decision) | medium |
| Trend ingestion service / cron / manual upload flow | Q1 (sourcing strategy) | LARGE |

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
