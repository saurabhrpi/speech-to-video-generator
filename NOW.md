# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 70 — 2026-05-19/20 — branch `v2`

**Status:** Beat It template shipped end-to-end (NBP → Kling → R2 → Firestore PUBLISHED, in new `mj_dances` row). 1 of 5 new V2.1 dance templates complete. V2.0.0 still in App Review. V2.0.1 backlog grew significantly with bugs surfaced during real-iPhone testing of Beat It.

## What happened this session

**Template-creation runbook written + locked.** `docs/V2_template_creation_runbook.md` + pointer in CLAUDE.md. Step-by-step procedure for V2 dance templates: source assets → Pillow-crop PNG → write `test_<slug>_chain.py` (bespoke NBP prompt for marketing preview only — production uses generic regen) → upload driving video to R2 → run NBP → review → run Kling → review → upload preview → write `seed_<slug>_template.py` (DRAFT) → sim test → flip published. User flagged hard early on that I'd deviated from the per-template sister-script pattern (had bundled into a generic CONFIG dict); reverted + documented to prevent recurrence.

**Beat It template — 5 iterations to land.** Started with 576×1024 TikTok-downloader source + dark dusk-alley NBP scene → Kling output had "floating dancer" + "jacket disappears" artifacts. Diagnosed two compound issues: (1) low-res driver loses pose detail, (2) dark-on-dark NBP scene loses silhouette contrast. Fixed in stages:
- **(v1)** Upscaled Beat_It_clip.mp4 576×1024 → 1080×1920 via Replicate `lucataco/real-esrgan-video` (~$0.02, 226s). Required URL-input (not local file) — see new memory.
- **(v2)** Discovered TikTok+username watermarks bouncing across the frame; user pulled a no-watermark TikTok export with only "channeling that MJ energy" text caption remaining. My delogo box was too tall (h=110) and overlapped the smoke detector on certain frames → ceiling artifacts. Tightened to h=60; still hit the dancer's arm at peak-extension frames.
- **(v3)** Switched to stream-copy crop of the no-watermark clip with text-caption intact; gambled on Kling ignoring it. Output much better but dancer still "floated" — ground plane mismatch (driving video had parquet floor; my NBP edit had alley asphalt).
- **(v4)** Regenned NBP edit with indoor industrial loft (hardwood floor + brick + warm pendants). Floor matched; floating reduced but not eliminated.
- **(v5, final)** User provided alternate source `Beat_It_YT.mp4` — different dancer in MJ Beat It cosplay (red jacket), static camera, hardwood floor, LCD TV with original Beat It MV playing in left ~35% of frame. Concern that Kling would get distracted by the LCD; tested + masked version, user rejected mask as "horrible" (black box obscured dancer's arm at extensions). Went raw with LCD intact → Kling handled it cleanly, accepted as final.

Beat It final state: `viral-dances-beat-it` PUBLISHED, `category=mj_dances`, `audio_enabled=True`, `credit_cost=25`, `use_nbp_regen=True`, `nbp_framing_hint="Composition: full body standing pose, head to feet."`. Driver + preview on R2. CDN purged + verified byte-identical to local.

**New "MJ Dances" row landed.** Beat It moved from `viral_dances` to `mj_dances`. Discovered + memorialized that `ref.update({field})` does NOT bump `updated_at`, so the `/api/templates` ETag stays the same and mobile 304s indefinitely — user reported "not showing on iPhone" → diagnosed → bumped `updated_at` via `SERVER_TIMESTAMP` → ETag changed → iPhone saw new row immediately. `mobile/app/index.tsx` has `CATEGORY_LABEL_OVERRIDES` mapping `mj_dances → "MJ Dances"` but that change rides V2.0.1 — current V2.0.0 binary renders the label as "Mj Dances" (mechanical title-case) until then.

**Memories added/updated:**
- `reference_replicate_url_input_only.md` — local file upload to Replicate is busted; pre-upload to R2 and pass URL. Misleading "Cog: upload output files" error with <10s predict_time = INPUT-fetch crash.
- `reference_firestore_partial_update_etag.md` — partial updates don't bump `updated_at`; clients get 304s forever. Include `updated_at=SERVER_TIMESTAMP` in every partial update.
- `project_kling_audio_test_policy.md` UPDATED — dance templates ship with `audio_enabled=True`; home-tile mutes client-side via `isMuted`; V3 will introduce audio-swap. Superseded the S66/S67 "default off" stance.

**V2.0.1 backlog grew significantly (locked S70):**
- Existing: AIV-92, version label fix, CLAUDE.md credit-constant drift fix, app.json buildNumber bump 14→15.
- **NEW: iOS audio fix** — call `Audio.setAudioModeAsync({ playsInSilentModeIOS: true })` in `_layout.tsx`. Without it, video audio honors iPhone silent switch (verified by user on real device — no sound until they flipped the side switch).
- **NEW: MJ Dances category label** — already in code (`CATEGORY_LABEL_OVERRIDES` in mobile/app/index.tsx), needs to ship.
- **NEW: Share-button second-tap bug** — `mobile/app/clip/[id].tsx:57-60` throws "Destination already exists" because dest dir from prior Share persists. Fix: `if (dest.exists) dest.delete(); dest.create();` before download. User repro at `~/Downloads/Sharing_Failed_Error.png`.
- **NEW: Home-screen CPU + scroll behavior** — with MJ row, currently 5 concurrent video decoders (1 hero + 3 row-1 + 1 row-2). Competitor pattern: 2.5 tiles per row + pause+dim hero on scroll. **Locked S70**: tile width 33% → **45%**, `viewabilityConfig.itemVisiblePercentThreshold` 50 → **100**, initial `visibleIds` seed 3 → **2**, hero `isActive={... && scrollY < HERO_H}` + animated black overlay 0→0.5 opacity across 0→HERO_H scrollY. All in `mobile/app/index.tsx`.

## Next step — Session 71 (on resume)

**Continue V2.1 template rollout (4 more):**

Priority order based on source quality:
1. **Pinky Up** — source already 1080×1920, no upscale. Pillow-crop PNG → write `test_pinky_up_chain.py` (pastel-pink hoodie + black biker shorts + white sneakers, pink-painted studio with soft neon accent — S70 approved direction) → NBP review → Kling review → seed.
2. **Rasputin** — source already 1080×1920, no upscale. Same flow. Approved direction: black turtleneck + brown corduroy + boots, smoky lounge with red velvet drapes + warm chandelier.
3. **Smooth Criminal** — source 576×1024, needs Replicate upscale first (use `scripts/upscale_driving_video.py` — URL input, FHD). Then same flow. Approved direction: tailored grey blazer + grey trousers + white sneakers, marble lobby with brass railings.
4. **Bad** — source 576×1024, needs upscale. Same flow. Approved direction: charcoal hoodie + black ripped jeans + chunky sneakers, dimly-lit subway platform with tile walls. Category: `mj_dances` (with Beat It). Smooth Criminal also goes to `mj_dances`.

**Tactical reminders:**
- Per-template flow lives in `docs/V2_template_creation_runbook.md` — follow it verbatim.
- Each template costs ~25 Kling credits + a few cents NBP + R2 storage. Real-world spend per template ~$2-3.
- After each preview is accepted, upload via `upload_template_assets.py`, purge CF cache, seed Firestore as DRAFT.
- Verify production gen path on iPhone before flipping any of them to published (use `set_template_status.py`). Beat It is currently PUBLISHED but production gen path has NOT been verified — user moved on to other things mid-test. Worth flagging.

**V2.0.1 work (after V2.0.0 lands):**
- All items above plus the 4 new ones logged in section 3 of the previous list.
- One commit, EAS build, TestFlight submit. Metadata-only ASC update is sufficient (no new screenshots required unless we want to refresh the paywall one from a true 6.9" device).

## Open questions

1. **(Medium, NEW S70) Beat It production gen path unverified.** Status is PUBLISHED; preview tile works on iPhone. Real end-user gen (upload selfie → Generate → confirm production NBP-regen path produces coherent output) was never completed before user pivoted to other tasks. If V2.0.0 ships before this is verified, real users will burn 25 credits on potentially-broken output. Recommendation: flip Beat It back to DRAFT until verified, OR verify it now via iPhone gen.
2. **(Medium) RC Test Store prices for dev parity.** Update `pro_pack_50/120/250` prices in RC's Test Store catalog to match production ($5.99 / $15.99 / $24.99). Currently stale on dev sim. Not blocking launch.
3. **(Medium) Bombale published-status drift** (S64 carryover). Spot-check during V2.0.0 review window.
4. **(Low) Coherence prompt scope.** Now 4 published templates (Bombale + Gangsta + Baby Dance + Beat It); after Smooth Criminal + Pinky Up + Bad + Rasputin land, could lock as dispatcher-only and drop per-doc duplication.
5. **(Low) Pattern smell on spike scripts.** Now 5 near-identical `test_*_chain.py` + 4 near-identical `seed_*_template.py`. Generalize after all 5 templates land (V2.1 ship complete) — NOT mid-build.
6. **(Low) Adult-on-baby-dance preview.** Preview shows the child stand-in; runtime applies child motion to adult selfie.
7. **(Low, S69) CLAUDE.md credit-constant drift.** `_ANON_STARTER_CREDITS = 10` listed; actual is 25. Fix in V2.0.1.
8. **(Low, S69) Stale version label.** `mobile/app/settings.tsx:97` hardcodes "AIVO v1.0.0". Bump to 2.0.0 in V2.0.1.
9. **(Low, NEW S70) Auto-bump `updated_at` on Firestore template writes.** Worth considering as a write-through hook in `template_registry.py` so future partial updates can't desync the ETag. Current workaround: include `updated_at=SERVER_TIMESTAMP` in every partial update, or use `upsert_template` (full replace).
10. **(Low, NEW S70) `scripts/upload_template_assets.py` only matches canonical basename slots.** Tried to upload `driving_video_v2.mp4` — got "skip non-canonical file" warning. Would need a `_manifest.json` to whitelist. Worked around by calling `r2_client.upload_file` directly. Worth either: (a) extending the uploader to take an explicit key, or (b) documenting the `_manifest.json` escape in the runbook.
