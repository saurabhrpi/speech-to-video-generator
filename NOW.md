# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 77 — 2026-05-25 — branch `v2`

**Status:** 5 new dance templates published + Beat It preview improved; a catalog-wide mobile-playback fix (streaming previews) + R2 filename↔role migration shipped & verified on iPhone; runbook updated to the new locked shape. The Hills (Girl Dances) Kling done but unpublished. Mac storage reclaimed 9→~47 GB.

## What happened this session

**Templates — feed now 17 published.**
- **Iconic Dances:** Cotton Eye Joe, Twist and Shine (Klings from S75 — seeded + published).
- **Viral Dances:** Na Favelinha (woman/casual/home), Dance Flow (similar man, EU seaside-hotel balcony + beach), Mapopo (recolored toddler girl; driver 2k-upscaled then re-timed — see below).
- **Beat It** preview re-trimmed to 14.63s (end-dup mitigation), re-uploaded + CF purge. Verified on iPhone.

**The Hills (Girl Dances) — Kling DONE, NOT published.** Output: `~/Downloads/the_hills_chain_66b624fb.mp4` (15.73s). NBP edit: `the_hills_edit_a3929c33.jpg`. Driver on R2 at `viral-dances/the-hills/`. Reference frame taken at **t=1s** (upright/face-visible — the 0.5s start frame was a faceless hair-flip; see runbook "force face visibility"). Awaiting review → seed+publish or iterate.

**Streaming previews (catalog-wide, PERMANENT).** Raw Kling previews were 14-35 Mbps @ 1440² → stuttered on mobile (start-stop/rebuffer). Re-encoded all 17 to ~5 Mbps + faststart via `scripts/streaming_previews.py`; `preview_video_url` now points at `preview_stream.mp4`. Verified smooth on iPhone. Revert lever: `streaming_previews.py --revert`.

**Filename↔role migration (`scripts/migrate_driver_filenames.py --execute`).** R2 names now match roles across all 17: `raw_source.mp4` (source/revert), `driving_video.mp4` (high-bitrate Kling output = runtime driver), `preview_stream.mp4` (app). Verified live + a gen worked on iPhone.

**Mac storage:** 9 GB → ~47 GB free (DerivedData + iOS DeviceSupport ~21 GB; 4 non-primary sims ~15 GB; .dmg installers ~2.7 GB). Primary sim iPhone 17 Pro Max preserved.

**Runbook** rewritten to the S77 shape (artifacts table + "filename ≠ role" caveat + going-forward flow + inline ⚠️ pointers on steps 2/5/9/10/11).

## Next step — Session 78

1. **The Hills:** review `the_hills_chain_66b624fb.mp4` → seed+publish under **Girl Dances** (category `girl_dances`, title-cases clean, no override) or iterate. Follow the S77 runbook shape (`raw_source`/`driving_video`/`preview_stream` + `streaming_previews.py`).
2. **V2.0.1 ship work** (S74→S77 carryover, still pending): AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(NEW S77)** Streaming-preview monitoring — watch playback + gens for a few days. If good → AIV-107: fix the buggy `migrate_driver_filenames.py --cleanup` (no-op; see its docstring) and delete the orphaned high-bitrate R2 files.
2. **(NEW S77)** Rest of the **Girl Dances** sources are staged unprocessed in `~/Downloads/App Templates Prep/Working/Girl Dances/` (Buttons, Give it up, Like a G6, Pole Dance, Pour it Up, River, Stateside, Telephone, Woman).
3. **(S76→S77)** Other shipped templates' previews may carry the Kling ~0.5s audio-lead — only DPWM/Beat It audited (AIV-105 In Review).
4. **(S75→S77)** Bad moonwalk — AIV-103. Next retry = Kling I2V w/ text prompt, ~$2 ceiling. Undecided: retry vs drop.
5. **(S74→S77)** UX risk: users see pro previews but get v2.6-std runtime output. Accepted; revisit if complaints.
6. **(S74→S77)** AIMLAPI `nano-banana-pro-edit` for NBP-edit repositioning — worth investigating.
7. **(S76→S77)** NBP runtime dependency hardening — AIV-106 (billing SPOF + preview-model risk).
