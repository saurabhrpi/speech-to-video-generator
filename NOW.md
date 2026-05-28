# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 82 — 2026-05-27 — branch `v2`

**Status:** **7 new `tiktok_dances` templates published** → feed **29 → 36**. All committed + pushed on `origin/v2`. Per-template artifacts (chain + seed scripts) committed. No mobile changes this session — the S81 mobile edits (TikTok label, hero threshold) are still **UNRELEASED** (part of the V2.0.1 batch).

## What happened this session

- **7 templates shipped** (all Pipeline A, tiktok_dances, 25cr, audio on, v2.6/pro/video): **Soda Pop Baby Dance** (reused the live Mapopo baby — direct frame, NO NBP roll), **Freeze** (new woman, night restaurant; audio-lead-corrected), **Dale Pa Ve** (Latina woman, Zumba studio; tail-cropped to 14.5s for end-dup), **Lush Life** (new woman, beach sunset, crochet dress — re-rolled once for a distinct outfit/identity), **Raindrop** (new woman, neon rooftop — redirected off the parking lot to avoid cloning High School), **Big Guy** (new woman, meadow; audio-lead-corrected; footwear added via a preserve-pass edit), **Soda Pop Energy** (new man, countryside field; shipped with the **original Kling lead intact** per user preference).
- **Audio-lead TWIN-driver fix + runbook correction (the big lesson).** `driving_video.mp4` must be the high-bitrate **twin of the corrected `preview_stream.mp4`** (same content, corrected identically if a fix is applied) — NOT the raw uncorrected output. Caught a near-miss on Freeze pre-upload. Audited the catalog: Soda Pop + High School + Pinky Up + Let's Go were all consistent (uncorrected twins). Fixed `docs/V2_template_creation_runbook.md` (asset table, new "twin invariant", step 8b now builds BOTH from the corrected master) and **retracted the wrong "Kling re-applies the lead on every output" claim** (it was only ever confirmed on `pro`; runtime is `std`; per-gen variance kills a static `audio_offset_sec`, which isn't even implemented — AIV-105 open). The +0.5s head-trim's UX tradeoff (silent open vs lost footage) is a per-template judgment call — see updated [[feedback_kling_audio_lead_and_preview_propagation]].
- **New memory** [[feedback_persist_accepted_nbp_edit]] — never delete the FINAL accepted NBP character edit; it's the only clean reuse source (Mapopo-baby reuse forced a lossy frame-grab from the compressed output video).
- **Gemini deprecation triage (no action needed).** The "Agent Platform" email doesn't touch us — we run AI Studio + `gemini-3-pro-image-preview`, not the listed flash models. Our model has **no announced shutdown** (don't confuse with `gemini-3-pro-preview`, the TEXT model, which shuts 2026-03-09). Migration when it comes = flip `NBP_MODEL` (config.py:65) + the chain scripts' hardcoded `MODEL`; existing templates' baked assets never need rebuild (only runtime NBP regen depends on the live model).
- **Process:** Kling chain scripts now run via `run_in_background` (foreground was blocking the turn / "hung" during gens).

## Next step — Session 83

- **More `tiktok_dances` templates** from `Working/`: 7:11, Baby_Boo, Copacabana, Got 2 Luv U, Luku, Soda Pop Moves, Speed. Flow is muscle-memory (inspect → confirm subject/scene direction → trim → upload raw_source → chain `--no-kling` approve → Kling `--keep-audio` (background) → twin driver+preview → seed (auto-poster) → publish). **Seteadora = SKIP** (flagged poor candidate: back-to-camera = Kling tracking risk + twerking = reviewer-safety risk; neither fixable by NBP since motion comes from the driver).
- **Resume V2.0.1 ship work** (now also carries the 7 new templates, on top of S80/S81 home-feed overhaul + posters + thumbnail/gate + TikTok label + hero threshold): AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(S82)** Sim test SKIPPED for all 7 S82 templates (live, not in-app verified). Spot-check tile playback + an end-to-end gen. Same gap as S81 Q.
2. **(S82→AIV-105)** Audio-lead RUNTIME sync still unverified for the current config (v2.6-std + raw-driver). Runbook now says verify with ONE real gen; no static fix exists (per-gen variance). Big Guy + Freeze shipped audio-corrected previews; Soda Pop Energy shipped with the lead.
3. **(S82→AIV-110)** Cleanup `~/Downloads/` intermediates this session: `*_chain_*.mp4`, `*_edit_*.jpg`, `*_shift_*.mp4`, `*_driving_video.mp4`, `*_preview_stream.mp4` for all 7 slugs (+ `mapopo_baby_video.mp4`, `Mapopo_Frame.png`). Per [[feedback_persist_accepted_nbp_edit]], KEEP the final accepted `*_edit_*` rolls. Carries S81's `lets_go_*`/`pinky_up_*`/`high_school_*` + `viral-dances/woman/raw_source_2k.mp4`.
4. **(S81)** Hero freeze threshold = 0.6 — tune if the partial-freeze reads odd on device.
5. **(S79→AIV-109)** Non-Kling motion-transfer model — needs the competitor app name (user has it) → research → `docs/research/`. River source kept.
6. **(S78→AIV-110)** Stale-artifact cleanup on R2 — `the-hills/driving_video_2k.mp4`, `give-it-up/raw_source_2k.mp4`, `spike-outputs/`. Runbook: `docs/template_prep_cleanup_runbook.md` (safe-ID = cross-ref Firestore URLs, never filenames).
7. **(S77→AIV-107)** streaming-preview monitoring, then fix buggy `migrate_driver_filenames.py --cleanup`.
8. **(S76→AIV-105/106)** Kling audio-lead audit beyond DPWM/Beat It; NBP runtime dependency hardening (billing SPOF).
9. **(S74)** UX risk: users see pro previews but get v2.6-std runtime output. Accepted; revisit on complaints.

**Deferred memory:** if NBP outpaint-widen recurs, amend `feedback_nbp_cant_reposition.md` (NBP CAN add lateral room via an outpaint-framed edit, CANNOT zoom-in a subject → use Pillow crop). [S78; carry until re-confirmed.]
