# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 87 — 2026-05-31 — branch `v2`

**Status:** V2.0.1 — coins/pricing rework SHIPPED to code + Firestore + ASC; EAS build #16 (v2.0.1) built; a gen-killing backend bug found and fixed. **Next session opens with: sim-test all the changes** (user will do), then redeploy backend + finish the ship sequence. Two things still genuinely open: the **Firestore-script hang** (tracked as an open problem) and **migration-completeness verification** (blocked by that hang; user's live balance is the real-world check).

## What happened this session

- **Pricing rework — shipped.** Redenomination **100 coins = $1** (was 10/$1): pack grants ×10 (`pro_pack_50/120/250` → **500/1500/2500**) in both `credits.py` (source of truth) + mobile `constants.ts`; **fixed the pre-existing middle-pack bug** (mobile showed 150, backend granted 120 → now 1500 both). **Flat per-video price = 500 coins ($5)** for all templates (was 25) — applied, **45/45 written**. Anon starter **25→500** (one free gen). Legacy S2V cost ×10. Committed `b611fca`, backend deployed by user.
- **ASC (by user):** IAP Display Names → "500/1500/2500 Coins" (Product IDs immutable + invisible; prices kept $5.99/$15.99/$24.99). RC untouched. Coin-icon screenshots deferred to post-build (capture from paywall on #16; no ticket).
- **Clickable balance:** home top-right balance is now a `Pressable` → opens paywall. Generate gates (template + S2V) already routed to paywall on shortfall — confirmed, unchanged.
- **EAS build #16 (v2.0.1):** bumped marketing `version` 2.0.0→2.0.1 (manual; buildNumber EAS-auto-incremented 15→16, write-back committed). Build finished. **Not yet submitted to TestFlight.**
- **🔴 Gen-killing bug found + fixed:** every template gen crashed with `name 'time' is not defined` (user hit it live; `~/Downloads/Error_Screenshot.png`). Root cause: `video_service.py` used `time.time()` in the motion-transfer dispatch with no top-level `import time` (inline imports were in *other* functions / after the use). Fixed (`42b6372`), pushed — **needs backend redeploy** to take effect. Swept the whole app with `ruff --select F821,...` (scope-aware) + `tsc`: **no other undefined-name bugs** anywhere.
- **Settings close button:** added ✕ (router.back()) — modal route had no dismiss affordance (user report). `491a480`.
- **Balance migration ×10 — PARTIAL/unverified.** Idempotent + marker-guarded; first `--apply` committed only *some* of 34 ledgers before the Firestore client hung. User's ledger was a straggler (showed 100) — **user fixed it by hand in Firebase Console** (→1000). Migration completeness across all ledgers is **still unverified** (blocked by the hang).
- **Template-prep cleanup (AIV-110 local half):** deleted 104 redundant files (~2.0 GB → 56 MB) from `~/Downloads/App Templates Prep/`, R2-verified each first; kept 41 irreplaceable.
- **Process: 6 memories written** (all committed; one casing bug fixed — see below). Notably the Firestore hang is captured as an **open problem to solve**, not a solved one.

## Next step — Session 88

1. **SIM-TEST all S87 changes first (user)** — run the Step 2 smoke checklist on the sim: balance shows ×10 / migrated value, template price = 500, top-right balance opens paywall, packs read 500/1500/2500, **a real gen completes** (validates the `import time` fix end-to-end), shortfall → paywall, Settings ✕ dismisses, hero pages 7, AIV-96 picker opens.
2. **Redeploy backend** so the `import time` fix is live before the on-device gen test (the committed fix is inert until redeploy).
3. **Verify migration completeness** — confirm all 34 ledgers carry `redenom_v2_applied` + balances ×10. BLOCKED by the Firestore hang (open problem #1 below) — may need the Console or a server-side run.
4. **Ship sequence (Steps 3–4):** 18+ age-rating questionnaire (ASC), confirm EU exclusion, coin-icon IAP screenshots from #16's paywall → `eas submit` to TestFlight. **Submit-to-review still gated on the IP/likeness audit.**
5. **IP/likeness audit** — the one hard pre-launch gate (Linear Urgent); per-template clearance pass.

## Open questions

1. **(S87) 🔴 Firestore-script hang — UNSOLVED open problem.** firebase-admin scripts hang forever from local env; `timeout=` did NOT cure it (doesn't bound the google-auth token fetch); not yet root-caused. Path to fix in `memory/feedback_firestore_script_hang_unresolved.md` (probe where it blocks → fix the proven layer / run server-side / wall-clock guard). Blocks bulk Firestore ops + migration verification.
2. **(S87)** Migration completeness unverified (see #3 above) — user's own ledger fixed; the other 33 not confirmed.
3. **(S86)** Per-asset **IP/likeness audit** — the one hard submit gate (Linear Urgent).
4. **(S86)** Counsel once-over of the live legal docs (face uploads + China processors) before broad release.
5. **(S87)** Linear hygiene: close shipped issues (pricing rework, clickable balance, settings close, `import time` fix; + S86's privacy rewrite, AIV-42, AIV-97, home carousel).
6. **(S85)** Age-rating questionnaire answers (ASC) for the 18+ maturity bump.
7. **(S85)** Admin R2 token from the lifecycle apply can be **revoked now**; app stays on its object-scoped token.
8. **(S87)** `Memory/` dir casing: git tracks capital `Memory/`; a lowercase `git add memory/...` silently stages nothing on the case-insensitive FS (cost us 4 untracked memories until caught). Always `git add -A Memory/`. Consider normalizing the path the wake protocol uses.
9. **(S83→AIV-105)** Audio-lead RUNTIME sync unverified for v2.6-std + raw-driver.
10. **(AIV-110/109/107, S81)** AIV-110 **R2-side** stale-artifact cleanup still open (local half done S87); AIV-109 non-Kling competitor research; AIV-107 streaming-preview monitoring; hero freeze threshold 0.6 tune; onboarding polish.
