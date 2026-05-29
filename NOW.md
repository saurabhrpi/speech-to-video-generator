# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 83 — 2026-05-27 — branch `v2`

**Status:** **6 new `tiktok_dances` templates published** → feed **36 → 42**: 7/11, Seteadora, Copacabana, Speed, Got 2 Luv U, Luku. **2 more mid-flight**: Soda Pop Moves (Kling output downloaded, twins/seed/publish pending), Baby_Boo (NBP edit pending user verdict). Push-style Kling monitoring pattern introduced. Originally `Seteadora` was flagged SKIP in S82 but shipped this session per user override.

## What happened this session

- **6 templates shipped** — 7/11 (tropical poolside, white woman dark hair, +0.5s audio fix), Seteadora (nightclub w/ empty dancefloor v2b after crowd-removal Pattern A edit; Latina, audio in-sync), Copacabana (cocktail lounge v2 lateral-room re-roll; Latino man; +0.5s audio + head+tail 0.5s trim), Speed (highway-at-night v2 shoulder Pattern A re-edit; South Asian man; audio in-sync), Got 2 Luv U (living room v3 lateral-room re-edit; mixed-race woman; audio in-sync), Luku (suburban backyard; older "dad" white man 50s-60s; audio in-sync).
- **Push-style Kling monitoring locked in.** New `scripts/monitor_kling_task.py` polls Kling in background and exits on terminal state. New per-template flow: inline-python `client.submit()` (~3s) → spawn `monitor_kling_task.py` via `run_in_background` → harness re-invokes assistant on monitor exit. Replaces the chain script's inline 600s `generate_and_poll`, which burned conversation context on slow gens.
- **Big lesson + memory update — lateral room prevents face distortion.** Updated [[reference_kling_mc_aspect_inherits_nbp]] with S83 finding: cramped framing in NBP edit causes BOTH cramped dance AND **face distortion** in Kling output (not just out-of-frame clipping). Original Copacabana had booths within arm's reach → first Kling output had cramped arms + subtle face distortion. Pattern A re-edit pushing furniture out fixed both. Going forward, every Pattern B chain prompt bakes the explicit "55-65% frame height, EQUAL open floor on both sides, nothing within arm's reach" clause up front (Luku, Soda Pop Moves, Baby_Boo).
- **Big lesson + memory update — false-positive hangs.** Got 2 Luv U v3 monitor exited HUNG (code 2 at 300s no `updated_at` change), but a direct poll right after showed `task_status: succeed` — saved a wasted $1.50 re-submit. New workflow rule: ALWAYS direct-poll once after monitor's HUNG exit before re-submitting (user-locked: poll ONLY after 300s of no monitor updates, never earlier). Discriminator: true hangs sit at `submitted`; false-positive hangs sit at `processing`. Memory amended at [[reference_kling_task_hang_detection]].
- **True hangs observed (no charge).** Seteadora v1+v2 sat in `submitted` forever — re-submitting fresh tasks worked. Per memory, hung tasks aren't charged. Kling API has NO cancel/delete endpoint — orphan tasks may eventually wake and produce a discardable output.
- **Process delta from S82:** chain scripts now invoke `client.submit()` directly (submit-only inline-python) followed by monitor in background, instead of full `generate_and_poll`. Cuts dead inline-poll time when Kling takes >10 min.

## Next step — Session 84

- **Finish Soda Pop Moves**: inspect `~/Downloads/soda_pop_moves_chain_888833.mp4`, decide audio-sync (apply +0.5s fix or ship-as-is), build twins, upload to `viral-dances/soda-pop-moves/`, write+run `seed_soda_pop_moves_template.py`, publish via `set_template_status.py`. → feed 42 → 43.
- **Finish Baby_Boo**: inspect `~/Downloads/baby_boo_edit_aa5be06d.jpg` (white blonde woman in patio-at-night, slip midi). If approved, submit-only Kling + monitor; else iterate NBP edit. Then twins / seed / publish. → feed 43 → 44.
- **Resume V2.0.1 ship work** (carries 14 new templates this batch + S80/S81 home-feed/posters/TikTok-label/hero-threshold from prior sessions): AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(S83)** Soda Pop Moves audio sync — needs user verdict (Kling output downloaded, twins not yet built).
2. **(S83)** Baby_Boo NBP edit — pending user inspection (left at `~/Downloads/baby_boo_edit_aa5be06d.jpg` at /close).
3. **(S83)** Hung Seteadora v1+v2 task IDs (888806253990903823 stayed in `submitted`; v2 888811813252104221 same) — no charge per memory, but theoretically could wake and produce orphan output. Untrackable per Kling API.
4. **(S83→AIV-110)** Cleanup `~/Downloads/` intermediates this session: `*_chain_*.mp4`, `*_edit_*.jpg`, `*_shift_*.mp4`, `*_driving_video.mp4`, `*_preview_stream.mp4` for all 8 S83 slugs (+ `seteadora_edit_v2_*`, `copacabana_edit_v2_*`, `speed_edit_v2_*`, `got_2_luv_u_edit_v2_*`/`_v3_*`). Per [[feedback_persist_accepted_nbp_edit]], KEEP the final accepted `*_edit_*` rolls (S83 finals: `seteadora_edit_v2_250479fc.jpg`, `copacabana_edit_v2_bd42d608.jpg`, `speed_edit_v2_c6d35f91.jpg`, `got_2_luv_u_edit_v3_5a405bb9.jpg`, `7_11_edit_573907df.jpg`, `luku_edit_009b0b4e.jpg`). Carries S82 + S81 cleanup backlog.
5. **(S83→AIV-105)** Audio-lead RUNTIME sync still unverified for v2.6-std + raw-driver (carry from S82). 4 of 6 S83 templates shipped audio-in-sync as-is; 2 (7/11, Copacabana) needed +0.5s. Per-gen variance still in force; no static fix viable.
6. **(S82)** Sim test continues to be skipped for S83 templates (14 published total since S82 without device-side spot-check). Spot-check golden-path gen + tile playback on sim.
7. **(S81)** Hero freeze threshold = 0.6 — tune if partial-freeze reads odd on device.
8. **(S79→AIV-109)** Non-Kling motion-transfer model — needs competitor app name (user has it) → research → `docs/research/`. River source kept.
9. **(S78→AIV-110)** Stale-artifact cleanup on R2 — `the-hills/driving_video_2k.mp4`, `give-it-up/raw_source_2k.mp4`, `spike-outputs/`. Runbook: `docs/template_prep_cleanup_runbook.md`.
10. **(S77→AIV-107)** Streaming-preview monitoring, then fix buggy `migrate_driver_filenames.py --cleanup`.

**Deferred memory:** If NBP outpaint-widen recurs, amend [[feedback_nbp_cant_reposition]] (NBP CAN add lateral room via outpaint-framed edit, CANNOT zoom-in a subject → use Pillow crop). [S78; carry until re-confirmed.] (S83 partial validation: Pattern A edits on existing NBP edits successfully pushed furniture/walls outward when prompted to "extend the open floor" — confirms NBP can compose a wider surroundings around a fixed subject, just not rescale the subject.)
