# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 80 — 2026-05-26 — branch `v2`

**Status:** Girl Dances row now **9 published** (added Pole Dance, Woman, Stateside, Like a G6); feed → 26; `Working/` source queue **clear**. Home-feed tile playback overhauled (viewport-gated + first-frame posters) — committed but **UNRELEASED** (`app.json` still 2.0.0 / build 15; part of the V2.0.1 batch).

## What happened this session

- **4 Girl Dances published** (`girl_dances`, Pattern B, v2.6/pro/video, 25cr, audio on): **Pole Dance** (kept the pole + preserve-framing since pole dance is anchored-not-lateral; purple/amber wall relight), **Woman** (2k Topaz-upscaled driver re-encoded ~14 Mbps, white woman + sofas + closer framing, end-trim 1s to drop an abrupt tail pose jump), **Stateside** (white woman, big clean-edged knee rips — legs through, not ragged), **Like a G6** (white woman, navy + gold heels, nightlife **REGEN** — a darken-edit left the subject daylight-lit; regen-framed prompt fixed it). Each: `test_<slug>_chain.py` + `seed_<slug>_template.py`.
- **Runbook fixes** (`docs/V2_template_creation_runbook.md`): template asset upload is a **direct `r2_client.upload_file`**, NOT the bulk `upload_template_assets.py` (it can't emit `raw_source`/`preview_stream` keys); steps 2/5/9 corrected; trimming made **conditional**.
- **Home-feed playback overhaul** (`mobile/app/index.tsx`, V2.0.1, UNRELEASED): outer `ScrollView` → vertical `FlatList` of rows; a tile plays only when `rowOnScreen` (≥90% row visible) **AND** within-row visible (≥70%); **mount `<Video>` only when visible** (expo-av holds a live AVPlayer per *mounted* Video regardless of shouldPlay → was exhausting iOS decoders → prod stutter + off-screen tiles playing + all-black). First-frame poster `<Image>` base so non-playing tiles show their first frame ("paused = first frame").
- **Poster thumbnails for all 26 published** via new `scripts/generate_template_thumbnails.py` (frame0 → `thumbnail.jpg` → `thumbnail_url`, partial-update ETag bump). Fixed **Bombale** (had a `placeholder.example` URL — generator now placeholder-aware) and **Baby Dance** (stale old-video frame; regenerated + `?v=2` cache-buster for the app NSURLCache).

## Next step — Session 81

- **Fold thumbnail-gen into the template runbook + seed** so new templates auto-get a first-frame poster (frame0 → `thumbnail.jpg` → `thumbnail_url`). The script exists but the runbook doesn't reference it → a new template would ship posterless (black off-screen tile).
- **Broader device testing** of the home-feed change (scroll-in reload across all rows on real hardware; add `posterSource` preloading only if a flash appears — none on sim).
- **Resume V2.0.1 ship work** (now also carries the home-feed fix + 40% tiles + posters): AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(S80)** Home-feed thresholds (90% row / 70% tile) accepted on sim — may tune on device. Mount-on-visible reloads a tile on scroll-in (no flash on sim; verify on device, add `posterSource` if needed).
2. **(S80→AIV-110)** New build intermediate to clean: `viral-dances/woman/raw_source_2k.mp4` (Topaz 2k driver).
3. **(S79)** AIV-109 non-Kling motion-transfer model — needs the **competitor app name** (user has it) → research → `docs/research/motion-transfer-providers-S79.md`.
4. **(S79)** Give It Up ships a slightly jumpy fast pose-transition (Kling interpolation limit, accepted) — revisit if AIV-109 lands a better model.
5. **(S78→AIV-110)** Stale-artifact cleanup — `the-hills/driving_video_2k.mp4`, `give-it-up/raw_source_2k.mp4`, `river/*` intermediates, `spike-outputs/`. Safe ID = cross-ref Firestore URLs, NEVER filenames.
6. **(S77→AIV-107)** streaming-preview monitoring, then fix buggy `migrate_driver_filenames.py --cleanup` (published-catalog R2 orphans).
7. **(S76→AIV-105)** Other shipped templates' previews may carry the Kling ~0.5s audio-lead — only DPWM/Beat It audited.
8. **(S75→AIV-103)** Bad moonwalk — Kling-MC-limits log; fix paths: Kling I2V / re-source / non-Kling (AIV-109).
9. **(S74)** V2.0.1 ship work pending (see Next step).
10. **(S76→AIV-106)** NBP runtime dependency hardening (billing SPOF + preview-model risk).
11. **(S74)** UX risk: users see pro previews but get v2.6-std runtime output. Accepted; revisit on complaints.

**Deferred memory:** if NBP outpaint-widen recurs, amend `feedback_nbp_cant_reposition.md` (NBP CAN add lateral room via an outpaint-framed edit, CANNOT zoom-in a subject → use Pillow crop). [S78; carry until re-confirmed.]
