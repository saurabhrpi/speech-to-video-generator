# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 78 — 2026-05-25 — branch `v2`

**Status:** Girl Dances row launched — **Buttons + The Hills published** (feed now 19). River (3rd Girl Dance) in progress: character image final, but the Kling output's head-motion doesn't faithfully track the source (camera-too-far → small face). Fix = upscale the driver; switched off slow Replicate to the new **Topaz Video API** (`scripts/upscale_topaz.py`) — validated, ~5 min/~$1.20. River upscale + re-gen deferred to S79.

## What happened this session

- **Runtime NBP roominess (committed `da20d2b`, pushed).** Generic runtime regen prompt now mandates roomy/spacious ambience + lateral-movement room (`video_service.py:_GENERIC_NBP_REGEN_PROMPT`). S77 carryover also committed (`3fdfb79`).
- **Buttons — PUBLISHED** (`girl_dances`). Crop t=1s→end; Pattern-B NBP (party wear tank+pants, roomy/centered/full-body — re-rolled 2× for visible feet); Kling pro/v2.6; trimmed to 13s; seeded + published.
- **The Hills — PUBLISHED** (`girl_dances`). Iterated framing (too-close → wider) + wardrobe (coral tank → black jeans + platform heels) + **evening/night ambience**, driven off a **Replicate-2k-upscaled+synced** driver (75 min!). Final output 15.3s. R2 = `driving_video.mp4`(Kling output, runtime driver) / `preview_stream.mp4`(~5Mbps) / `raw_source.mp4`(2k synced driver); CF purged. (orphan `driving_video_2k.mp4` left on R2.)
- **River — IN PROGRESS.** Floor/reclining dance; Pattern-B NBP matched source (bra-top, moody dark studio, different woman). Keeper character image = **`river_edit_cropzoom_v1.jpg`**. Driver = `viral-dances/river/raw_source.mp4` (14.55s; local copy `~/Downloads/river_driver_src.mp4`). Kling consistently truncates to ~11.97s — accept + trim. `scripts/test_river_chain.py` exists.
- **Topaz Video API path (NEW).** Wrote `scripts/upscale_topaz.py` against the official OpenAPI schema (`~/Downloads/video-12-25-updated.yaml`). Replaces slow Replicate for driver upscales. `TOPAZ_API_KEY` in `.env`.
- **Runbook updated** to S78: composition shift (roomy/wider/centered **supersedes** the S73 preserve-framing lock for static-camera drivers); `streaming_previews.py` has **no** `--template-id` (manual per-template encode documented); seed shape adds `preview_video_url_orig`; driver-upscale gotcha now prefers Topaz over Replicate.

## Next step — Session 79: finish River

1. **Upscale River driver via Topaz** (~5 min, ~$1.20 — est. 9-10 credits, already confirmed via free `--stop-after create`):
   `.venv/bin/python scripts/upscale_topaz.py --input ~/Downloads/river_driver_src.mp4 --output ~/Downloads/river_driver_2k_topaz.mp4 --scale 2 --model prob-4`
   (if `river_driver_src.mp4` is gone, re-download R2 `viral-dances/river/raw_source.mp4`). **Topaz preserves timing + audio → NO re-time/re-mux** (unlike Replicate).
2. **Upload** the 2k output to R2 (e.g. `viral-dances/river/driving_video_2k.mp4`), verify 206.
3. **Re-gen Kling** with the sharper driver + the keeper image:
   `.venv/bin/python scripts/test_river_chain.py --edited-image ~/Downloads/river_edit_cropzoom_v1.jpg --driving-video <2k URL> --keep-audio`
4. **Eyeball:** does the bigger face + sharper driver make the head-motion faithfully follow the source? If yes → trim to ~12s + seed (`seed_river_template.py`, copy `seed_buttons_template.py`, `girl_dances`) + publish (S78 asset shape).
5. **Commit S78 work** (uncommitted: `test_buttons_chain.py`, `seed_buttons_template.py`, `test_river_chain.py`, `seed_the_hills_template.py`, `upscale_topaz.py`, runbook edits) — user to confirm.

**TODO — deferred memory (write ONLY after confirmation, per save-memory-after-verification):**
- After the full Topaz upscale run is confirmed end-to-end (timing + audio preserved, output usable by Kling), write `Memory/reference_topaz_video_api.md`: fast/cheap driver-upscale path replacing slow Replicate; client `scripts/upscale_topaz.py` (its docstring has the full API facts — base `api.topazlabs.com`, `X-API-Key`, standard flow create[free estimate]→accept→PUT→complete-upload[trailing slash]→status[`complete`, `download.url`], models `prob-4`/`rhea-1`/`iris-3`, Starter $0.12/credit, OpenAPI YAML is authoritative not the prose docs).
- If outpaint-widen works again on another template, amend `Memory/feedback_nbp_cant_reposition.md`: NBP CAN add lateral room via an outpaint-framed edit ("extend the scene outward, add floor L/R") but still CANNOT enlarge/zoom-in a subject (rescale refusal) — for zoom-in use a Pillow center-crop. (S78 River: widen worked, zoom-in no-op'd → Pillow crop `river_edit_cropzoom_v1.jpg`.)

## Open questions

1. **(NEW S78)** River head-motion may still partly follow the source choreography's head turns even after upscale — accept (it's the dance) or pick a different River source if it reads wrong.
2. **(NEW S78)** Topaz video credit-consumption rate vs the published image-MP table is unconfirmed; River est. was 9-10 credits (~$1.20) — watch actual billing on first real run.
3. **(NEW S78)** Cleanup the orphan `viral-dances/the-hills/driving_video_2k.mp4` on R2 (redundant with `raw_source.mp4`).
4. **(S77→)** AIV-107: streaming-preview monitoring; then fix buggy `migrate_driver_filenames.py --cleanup` + delete orphaned high-bitrate R2 files.
5. **(S77→)** Rest of Girl Dances sources staged in `~/Downloads/App Templates Prep/Working/Girl Dances/` (Give it up, Like a G6, Pole Dance, Pour it Up, Stateside, Telephone, Woman) — note Pole Dance / Pour it Up skew provocative (reviewer-risk accepted by user; only a whole-app pattern moves the age-rating needle).
6. **(S76→)** Other shipped templates' previews may carry the Kling ~0.5s audio-lead — only DPWM/Beat It audited (AIV-105).
7. **(S75→)** Bad moonwalk — AIV-103 (retry Kling I2V w/ text prompt ~$2, or drop).
8. **(S74→)** V2.0.1 ship work still pending: AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.
9. **(S74→)** UX risk: users see pro previews but get v2.6-std runtime output. Accepted; revisit on complaints.
10. **(S76→)** NBP runtime dependency hardening — AIV-106 (billing SPOF + preview-model risk).
