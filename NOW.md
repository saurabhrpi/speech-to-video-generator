# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 84 — 2026-05-28 — branch `v2`

**Status:** **3 new tiktok_dances templates published** → feed **42 → 45** (Soda Pop Moves, Baby_Boo, Git Up). **Credits→Coins UX rebrand SHIPPED** (commit `486cef9`, then `c7d8d73` ff-merged to main). **Floating-status-pill + 5-min countdown UX + client retry are IN CODE but UNCOMMITTED** — held pending Kling-timeout redesign decision (see Next step). Plus a temporary `console.log('[gen-debug] job_id …')` in gallery-store to remove before committing.

## What happened this session

- **3 templates shipped** — Soda Pop Moves (43, first-roll approve), Baby_Boo (44; surgical NBP second pass removed overhead Edison string lights between v1 and v2 edits), Git Up (45; cup-positioning iteration — "her right hand" failed → "VISIBLE ON THE LEFT SIDE OF THE FRAME" worked; Kling rendered cups in BOTH hands which user accepted over empty-hands variant).
- **Credits→Coins migration** — gold-clover PNG (~/Downloads/Coin.png was actually AVIF-with-.png-extension → broke RN decode, looked like an "orange slice"; converted with `sips -s format png`, then user-approved a Pillow-generated alt). Asset reference centralized in `mobile/lib/assets.ts` (config-driven). Word "Credits" → inline CoinIcon next to numbers; "coins" in pure prose.
- **Template detail redesigned** — UPPERCASE title (28pt) + half-size mood subtitle (14pt); Add-your-photo + Cost labels removed; cost embedded in "Generate · 25 [coin]" button (U+00B7 middot). **16 weak template descriptions** ("Pinky up. 💅✨", "Let's go! 🔥🏀" etc.) rewritten to proper 4-word mood lines via partial-upsert Firestore batch.
- **Home polish** — per-tile cost removed (redundant per row), UPPERCASE tile titles, section headers 16→18pt. Home FAB conditional: large centered "Generate Video" (20% bigger) when idle; compact stretched "Generate" filling room next to status pill (`left:16 → right:264`, `height:60`) when a gen is in flight.
- **Countdown UX + retry (UNCOMMITTED)** — `mobile/lib/generation-status.ts` phase machine (counting → almost_ready → awaiting_retry → failed), 30s `useGenerationTick` hook, `<FloatingStatusPill>` (black/white, per-route placement: hidden on `/gallery`, centered on `/template/*`, right-anchored elsewhere; shared `bottom = max(insets.bottom, 24) + 8`, `height: 60`), gallery card redesigned to spinner + phase label + subtitle, gallery-store `tickAndRetryIfDue` watcher with `retryBody` persistence (`retryAttempts < 1` only).
- **CLAUDE.md correction + v2→main ff-merge** — stale "V1 live on App Store, Build #14" was wrong; V2.0.0 has been live since AIVO rebrand. Versioning convention trimmed to current-only (V1 / V2.1+ history removed per user). Fast-forward main = v2 (68 commits, 0 conflicts) — main was strict ancestor; no PR needed (sole dev).

## Next step — Session 85

**Lock + implement the Kling-timeout redesign** (open Q at /close). User-leaning proposal (4 pieces, confirm verbatim before coding):
1. **Rip out client-side auto-retry** from gallery store (`tickAndRetryIfDue` + `retryBody` fields + 30s watcher). Kling has no cancel endpoint → resubmit-while-in-flight doubles cost, doesn't speed anything up. Keep the friendly countdown UX, just don't auto-resubmit. See [[feedback_no_client_retry_for_uncancellable_jobs]].
2. **Stretch backend `max_wait`** 600s → 900s in `kling_motion_client.generate_and_poll` (or override at the call site in `video_service.py:981` and `:1155`). Kling MC v2.6+std variance is empirically 3–12 min (S83).
3. **Backend progress-stuck detection** — no `updated_at` change for ≥5 min → declare hung early, return failed (matches S83 push-monitor pattern; avoids waiting full 15 min on actually-dead tasks).
4. **Auto credit-refund on declared failure** — backend re-credits the UID's ledger so users aren't charged for nothing.

Then **commit the countdown UX + the redesign together as one S85 commit**. Remove the temporary `console.log('[gen-debug] job_id assigned:', …)` in `mobile/store/gallery-store.ts` before committing.

After that: **resume V2.0.1 ship work** (carry from S83) — AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(S84)** Kling-timeout redesign — confirm the 4-point proposal verbatim with user at start of S85. Without confirmation, the countdown UX commit is stuck in limbo.
2. **(S84→AIV-110)** Cleanup `~/Downloads/` intermediates this session — all `git_up_*`, `baby_boo_*`, `soda_pop_moves_*` chain/edit/preview/driver files; `git_up_first_frame.png`. Per [[feedback_persist_accepted_nbp_edit]] KEEP the finals fed to Kling: `baby_boo_edit_v2_b5de1b18.jpg`, `git_up_edit_cfda7d39.jpg` (both empty-hands and cup variants were rolled), `git_up_edit_v2_5c731e10.jpg`. Carries S83+S82+S81 cleanup backlog.
3. **(S83)** Hung Seteadora v1+v2 task IDs from S83 — no charge per memory, but theoretically could wake. Untrackable per Kling API.
4. **(S83→AIV-105)** Audio-lead RUNTIME sync still unverified for v2.6-std + raw-driver. 9 of 9 S84 templates shipped audio-in-sync as-is; consistent S83+S84 evidence the runtime path may not introduce the lead at all (was only ever confirmed on `pro`).
5. **(S82)** Sim test continues to be skipped for shipped templates — 17 templates published over S82+S83+S84 without device-side spot-check of golden path. (Coins-UX testing this session DID happen on sim, but didn't include a full template gen.)
6. **(S81)** Hero freeze threshold = 0.6 — tune if partial-freeze reads odd on device.
7. **(S79→AIV-109)** Non-Kling motion-transfer competitor — needs competitor app name → research.
8. **(S78→AIV-110)** Stale-artifact cleanup on R2 — runbook in `docs/template_prep_cleanup_runbook.md`.
9. **(S77→AIV-107)** Streaming-preview monitoring, then fix buggy `migrate_driver_filenames.py --cleanup`.
