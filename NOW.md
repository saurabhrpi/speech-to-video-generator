# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 88 — 2026-05-31 — branch `v2`

**Status:** 🚀 **V2.0.1 (build #17) SUBMITTED to App Store review.** Full ship-sequence prep done this session (age rating 18+, App Privacy, EU exclusion, IAP + 6.9" screenshots, description/promo/what's-new rewritten, App Review notes). iPad scaled-mode smoke test PASSED. Two risks carried into review **by choice**: IP/likeness audit (deferred) + Guideline 1.1.4 (risqué pole template). **Next session opens awaiting Apple's verdict.**

## What happened this session

- **Sim-tested all S87 changes — 9/9 green.** A real template gen completed end-to-end (validated the S87 `import time` fix against the redeployed backend; charged 500 coins). Confirmed: balance ×10, clickable balance→paywall, template price 500, packs 500/1500/2500, shortfall→paywall, hero pager, AIV-96 picker.
- **🔴→✅ Settings ✕ fix:** discovered S87's commit `491a480` ("Settings close button") never actually included `settings.tsx` — lost to the `Memory/` casing/staging trap; the working tree had NO ✕ either. Re-implemented as a `headerRight` ✕ (`<Stack.Screen>` + `router.back()`, mirrors gallery), verified live. Committed `46594e1`.
- **EAS build #17 (v2.0.1):** built off `5b38e72` (includes the ✕ fix); buildNumber auto-bumped 16→17 (write-back `bbfe6b5`); uploaded to ASC + **SHA-verified ours** (`5b38e72`).
- **Telemetry read worked from local env this time (no hang):** Pinky Up gen = **5min 55s** total (NBP prep 38s + Kling 5:15). Kling-dominated, within its 3–12min variance; breached the 5-min SLA, just under 6-min. Backend Kling poll budget = **600s (10min)**; mobile has **no independent timeout** → if it hadn't landed it would've waited ~4¾ more min before a `timeout` failure.
- **Firestore-hang open problem advanced (not solved):** ran the memory's step-1 probe → **network branch RULED OUT** (oauth2 + firestore curl fast-404) and a single READ returned <1s. Hypothesis sharpened: hang is **bulk-WRITE-specific or intermittent**. Candidate fix = **batch the writes** (WriteBatch/BulkWriter). Migration verification still parked. (memory updated, committed `5b38e72`.)
- **App Store submission prep (the bulk of the session, all in ASC):**
  - **Age rating → 18+** (deliberate over-rate; honest level: the genital-contact pole step = Apple "Sexual Content or Nudity," not mere "Suggestive Themes"). Learned the ASC **Edit only appears after creating a version** (memory `2c16f07`).
  - **App Privacy** verified — Diagnostics group = **Other Diagnostic Data only** (Crash/Performance unchecked; we run no crash/perf SDK).
  - **EU exclusion** confirmed (Manage → Europe = 0).
  - **Screenshots:** IAP review shot + 7 App Store shots processed (alpha-stripped; **upscaled 1284×2778 → 1320×2868** for the now-single 6.9" slot); swapped a toddler hero for a non-minor shot. Uploaded.
  - **Description** rewritten V1→V2 (selfie→dance, coins pricing corrected) + promotional text + what's-new + App Review-note edits.
  - **iPad Air 13" scaled-mode smoke test → PASS** — paywall/IAP/template/picker all render + responsive (the exact #12/#13 rejection spot is clear). Tested via dev build (same RN layout as #17).
  - `eas submit`: build was already uploaded (SHA-verified ours); "build number already used" was benign. Attached #17 → **Submitted for review.**
- **Housekeeping:** fixed stale `$4.99`/credits pricing in CLAUDE.md → live coins values; 4 memories committed (✕-fix, firestore update, buildNumber, ASC age-rating; + 1 new this close).

## Next step — Session 89

1. **Await Apple's review verdict** on V2.0.1 build #17. Most-likely rejection vectors = the two deferred risks: **Guideline 1.1.4** (risqué pole template) or **IP/likeness**. Respond per the rejection email.
2. If **approved** → choose release (manual/phased) + start post-launch items.
3. **Linear hygiene** — close the pile of shipped issues (see open Q).

## Open questions

1. 🔴 **(S88) Firestore-script hang — UNRESOLVED.** Network ruled out + single-read works; suspect bulk-write-specific/intermittent. Candidate fix = **batch the writes**. Blocks bulk Firestore ops + migration verification. (`feedback_firestore_script_hang_unresolved.md`)
2. **(S87→S88)** Balance migration ×10 completeness (34 ledgers) still **unverified** — parked, to do with the batched-write attempt (user's own ledger was hand-fixed).
3. **(S86→S88, now a LIVE review risk)** **IP/likeness audit** — deliberately deferred into review; per-template clearance not done.
4. **(S88, LIVE review risk)** **Guideline 1.1.4** — the genital-contact pole template is the likeliest rejection trigger (18+ does not exempt overtly-sexual content); accepted risk.
5. **(S86)** Counsel once-over of the live legal docs (face uploads + China processors) before broad release.
6. **(S87→S88)** Linear hygiene: close shipped issues (pricing rework, clickable balance, settings ✕, `import time` fix, age-rating/privacy/screenshots/iPad-verify; + S86's privacy rewrite, AIV-42, AIV-97, home carousel).
7. **(S85)** Admin R2 token from the lifecycle apply can be **revoked** now (app stays on its object-scoped token).
8. **(S83→AIV-105)** Audio-lead RUNTIME sync unverified for v2.6-std + raw-driver.
9. **(AIV-110/109/107, S81)** AIV-110 **R2-side** stale-artifact cleanup (local half done S87); AIV-109 non-Kling competitor research; AIV-107 streaming-preview monitoring; hero freeze threshold 0.6 tune; onboarding polish.
