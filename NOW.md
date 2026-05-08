# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 58 — 2026-05-04 / 2026-05-07 — home-screen-redesign (closing)

**Status:** App V1 (S2V) APPROVED + LIVE on App Store. V2 vision locked: home-screen redesign with template carousels + motion-transfer wedge. Both motion-transfer outcomes verified end-to-end on a single-provider Kling architecture (Pollo dropped). Implementation plan saved at `docs/V2_motion_transfer_plan.md`. Backend Track 1 ready to start once 5 clarifying questions resolve.

## What happened this session

- **Apple approved Build #14 → app live on App Store.** Confirmed via "Welcome to App Store" email. App findable on Mac App Store via public link immediately; iPhone search indexing rolled in within 24h via developer-name search.
- **Real-device install + smoke test (production stack):** anon free-gen ✓, paywall trigger on 2nd attempt ✓, Apple Sign In completed (with documented two-attempt picker quirk — first picker silent-fails, second succeeds; memory `reference_apple_signin_first_attempt_fresh_sim.md` extended to "fresh sim AND first install from live App Store on real iPhone"), IAP purchase confirmed declined at "double-click to confirm" — real-Apple receipt → backend grant path remains untested, deferred to first organic purchase.
- **`hotfix-build14` → `main` merge complete + pushed.** New main HEAD `6aa2c2b` (merge commit). `home-screen-redesign` fast-forwarded to new main. Origin pushed. Three conflict resolutions: NOW.md (took theirs/stash for S57 body per "newest in body" convention), MEMORY.md + Apple-Sign-In memory (took ours/HEAD for S54 comprehensive content), `mobile/app.json` buildNumber → 14. **Conflict-resolution regression caught:** `--ours` on MEMORY.md silently dropped 6 S57 memory bullets — files survived as untracked, index entries vanished. Restored. New memory + CLAUDE.md Common Pitfalls rule: never blindly `--ours/--theirs` on index files.
- **Kling Motion Control v2.6 client scaffolded** (`src/speech_to_video/clients/kling_motion_client.py`). Direct API at `https://api-singapore.klingai.com`, HS256 JWT regenerated per request from `KLING_ACCESS_KEY` + `KLING_SECRET_KEY`, retries on GET only. PyJWT pinned in `requirements.txt`. Smoke-tested offline (JWT round-trip) + verified live on `/account/costs` endpoint (84 cr remaining of 100 trial after 4 generations).
- **Kling two-mode test (Outcome 2 verified, V1 plan locked for Outcome 2):**
  - `image` orientation + selfie + dance video → **clean Outcome 2** (1424×1456, photo AR, $1.12 COGS, ~5-6 min). User verdict: "Way better than Swaptok."
  - `video` orientation + headshot + full-body dance → Swaptok-grade fail. **Revised understanding (initially wrong):** both modes preserve photo background; canvas always matches photo AR. The `video` toggle is character-pose-within-photo-frame, not Outcome-1.
- **Kling pricing locked:** $0.14/cr post-trial (user-confirmed). 8 cr/gen at 10s `pro` = **$1.12 / 10s gen**. Earlier klingmotion.com "3 cr/s" estimate was advertised time-cost, not actual deduction.
- **Outcome-1 input-shaping spike — abandoned then unlocked:**
  - **v1 face-swap:** structural Outcome 1 ✓ but face fidelity broken (sunglasses contortion, dancer's hands/skin tone visible).
  - **v2 prompt:** introduced over-strip bug (would remove user's own accessories). Caught before run.
  - **v3 prompt with accessories-follow-second-image rule:** clean swap but final video still paste-in (face lighting didn't match scene). I declared "model-class ceiling, switch to Pollo." (**Wrong.**)
  - **`Match Video` digression:** retested video orientation with body-extended photo + scene-prompt → still Outcome 2 (confirms Kling is fundamentally Outcome-2 at structure level).
  - **v4 holistic-regen reframing (user proposal):** instead of "preserve everything except face," reframed as "regenerate a coherent photo combining identity-from-image-2 with pose/scene/lighting-from-image-1, naturally imagine missing body parts in user's clothing style." Same Nano Banana Pro Edit endpoint. **Clean Outcome 1.** User verdict: "Wow, this is gold."
- **V2 outcome strategy locked — single-provider Kling architecture.**
  - Outcome 2: Kling `image` mode. $1.12, ~5-6 min.
  - Outcome 1: Nano Banana Pro Edit (v4 regen prompt, ~$0.04) → Kling `video` mode ($1.12). Total **$1.16, ~7-8 min**.
  - **Pollo `mix` officially DROPPED.** No $80 API top-up needed. Viggle still de-prioritized.
- **V2 product vision laid out (user direction):** competitor-style home screen — top 1/3 hero carousel of viral trends (landscape), below = rows of theme-bucketed template carousels, no tabs, floating Create Video button → S2V (demoted), top-right profile icon → user gallery → gear → settings. Templates pulled from top-10 viral trends per theme on TikTok/IG. **Both outcomes ship day-one.**
- **Plan doc created at `docs/V2_motion_transfer_plan.md`** with vision, 2 load-bearing risks (TikTok/IG content licensing — CRITICAL; variance scaling across templates × selfies), 5 clarifying questions to user, 4-track work breakdown, recommended starting sequence.
- **Memory work this session:**
  - 4 new feedback memories: `feedback_provider_mode_names_neq_outcomes.md`, `feedback_index_files_need_handmerge.md`, `feedback_localized_edits_cant_holistic_regen.md` (then amended after v4), `feedback_regen_vs_preserve_prompts.md`.
  - 6 S57 memory bullets restored to MEMORY.md after the `--ours` conflict-resolution regression.
  - CLAUDE.md Common Pitfalls section gained the index-files rule (loaded into every session's system prompt).
  - `reference_apple_signin_first_attempt_fresh_sim.md` description+content broadened to cover real-iPhone-from-App-Store case.

## Next step — Session 59 (on resume)

1. **User answers 5 clarifying questions** in `docs/V2_motion_transfer_plan.md`:
   - Q1 (CRITICAL — legal): Trend ingestion strategy. Manual curation, paid trend-data provider, AI-generated approximations, or mix? Gates everything legal.
   - Q2: V2 theme list (Dance / Comedy / Transformation / Sports / Couples / Reactions / etc.).
   - Q3: Hero carousel content — same templates as below or distinct curated content?
   - Q4: Per-template outcome-assignment process (who decides 1 vs 2 per template).
   - Q5: Template asset hosting — S3 / Cloudinary / Bunny CDN / other?

2. **Backend Track 1 work I can start without waiting on Q1-Q5:**
   - `VideoService.generate_template_video()` — orchestration for both outcomes (Outcome-2 = direct Kling; Outcome-1 = Nano Banana regen → Kling).
   - First-frame extraction utility (ffmpeg via `imageio-ffmpeg`).
   - `POST /api/generate/template-video` endpoint (reuses existing job manager + concurrent-credit gate).
   - Template registry schema design (`outcome`, `published_status` flag for QA gate, etc.).
   - Variance-testing harness — extend `scripts/kling_outcome1_spike.py` to take input URLs as args so we can batch (template × selfie) tests.

3. **Variance testing in parallel (Track 3):** v4 pipeline tested on ONE input pair only. Need to test across different selfies (full-body, women, glasses, low-light) and different reference videos (non-dance content) before declaring production-ready. Cheap on remaining 84 trial Kling credits.

## Branch state at close

- On `home-screen-redesign` (now at `6aa2c2b` after fast-forward post-merge). Origin pushed for `main`; `home-screen-redesign` not pushed.
- `main`: at `6aa2c2b` (merge commit `Merge branch 'hotfix-build14'`). Pushed to origin S58.
- `hotfix-build14`: unchanged, points at `a432301`. Merged into main.
- **Working tree dirty (S57+S58 work uncommitted, intentional — committing per-feature post-resume):** NOW.md (this), `Memory/MEMORY.md` (index updates), `requirements.txt` (PyJWT), `src/speech_to_video/utils/config.py` (Kling settings), `src/speech_to_video/clients/kling_motion_client.py` (new), `scripts/` (3 spike scripts), `REQUIREMENTS.md` (S56), `docs/` reorg + `V2_motion_transfer_plan.md` + research log updates, 10+ memory files (mix of S57 carryover + new S58 ones), `docs/Hailuo_*.txt` etc. deletions (moved to `docs/api-notes/` in S57 reorg).

## Open questions

- **(S58 new — V2 GATING)** Q1-Q5 clarifying questions in `docs/V2_motion_transfer_plan.md`. Q1 (TikTok/IG content licensing) is the critical one — could kill the wedge.
- **(S58 new)** Variance testing across (template × selfie) combos before V2 production confidence.
- **(S58 new)** Pricing tier for Outcome 1 vs Outcome 2 (post backend, pre-launch). $1.12 vs $1.16 COGS, plus Apple's 15% cut. ~12-18 credits per gen feels reasonable; needs decision.
- **(S58 new)** Push-notification infrastructure — V2 has 7-8 min long-gens at the edge of "tap and wait" UX. Post-launch decision.
- **(S58 carryover)** First organic Apple IAP purchase. Sandbox/TestFlight validated; production grant path untested. Watch RC dashboard + backend logs on first organic transaction.
- **(S58 follow-up)** Real-device smoke test on physical iPhone — done ✓ (S52 carryover #6 closed). Identified the documented two-picker Apple Sign In quirk on production.
- **(S55 carryover)** Viggle key still pending. **De-prioritized** — Kling delivers both outcomes, no urgency.
- **(S53 carryover)** Dad's Apple Developer enrollment retry from home WiFi.
- **(S53 carryover)** M365/Entra tenant decision (ToDo #26).
- **(S48 follow-up B)** UX hole: home button shows action label only, balance only in Settings. V2 home-screen redesign may obviate or change this.
- **(ToDo #19, S49+S48)** CustomerInfo listener for offline-replay + RC ingestion-lag.
- **(ToDo #27, S54)** Verify concurrent-submit credit gate post-deploy.
- **(Yellow #10)** Backend Apple precheck + clip-merge — `/api/auth/apple/precheck` + `/api/clips/merge` existence not yet verified in `server.py`.
- **(S43-era, future trigger)** RC `default` offering "Current" implicit — flag if a second offering arrives and `getOfferings().current` returns null.
- **(S57 deferred — now mostly moot for V2)** Pollodance 2.0 Ref quality; Pollo other Mimic models for outcome-2; deepfake/consent legal risk for arbitrary user photo uploads (still relevant for V2 motion-transfer launch — pre-launch must).
