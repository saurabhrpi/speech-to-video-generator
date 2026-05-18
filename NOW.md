# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 67 — 2026-05-17 — branch `v2`

**Status:** V2.0.0 wired end-to-end on local. 3 Pipeline A templates live (Bombale hero #0, Gangsta hero #1, Baby Dance hero #2). App rebranded to AIVO (icon + splash + app.json `name`). Pricing locked at $5.99 / $15.99 / $24.99. `template.audio_enabled` schema in place, all templates currently silent. Awaiting user-side `expo prebuild`, ASC manual steps, and EAS build for TestFlight.

## What happened this session

**Two new Pipeline A templates shipped end-to-end.**
- **Gangsta** (`viral-dances-gangsta`, hero #1) — NBP Edit on `gangsta_reference.png` (outfit → beige blazer + white tee + light chinos, bg → lighter urban alley, UI overlay stripped) → Kling Motion Control → preview rendered → seeded Firestore → published. Audio-on test pass (`keep_original_sound="yes"`) — soundtrack clean, sync intact.
- **Baby Dance** (`viral-dances-baby-dance`, hero #2) — Same flow. Twist: where Gangsta's NBP run had cleanly stripped the X + caption strip on first try, Baby Dance's first two NBP runs (with increasingly emphatic prompts) both retained the overlays. Resolved by pre-cropping the input image (Pillow: crop bottom 19%, mask top-left 220×220 with sampled wall color) before passing to NBP — worked first try on the cleaned input. Output landed cleanly: lavender ruffle top + tiered pink tulle skirt + leggings, pastel forest mural playroom. Memory saved: `feedback_nbp_wont_remove_ui_overlays.md`.

**Mobile carousel now prefers `preview_video_url` over `driving_video_url`.** Tile/hero/template-detail screens fall back to driving only when preview is unset — so Bombale (preview null) stays as-is, Gangsta + Baby Dance show the Kling output (motion applied to a stand-in character).

**Hero pager page indicator.** Lined pills at the bottom of the hero (active widens, 18×4 vs 6×4 inactive). Auto-hides at <=1 hero. Renders on `onMomentumScrollEnd`.

**Category row sort.** `groupByCategory` sorts items within each category by `created_at` ascending so newly-added templates land at the end of the row instead of arbitrary Firestore order.

**`template/[id].tsx` close button fixed.** Same flow-layout HeaderRow refactor as `clip/[id].tsx` (S66) — replaced the absolute X overlay with a back chevron in flow layout. iOS was silently swallowing touches on the Pressable above the expo-av Video. NOW.md open question #3 resolved.

**Thumbnail retry with exp backoff.** `gallery-store` `runPoll` now retries `generateThumbnail` at 1s / 2s / 4s before falling through to the hydration backfill safety net. NOW.md open question #6 resolved.

**V2.0.0 pricing locked.**
- Anon starter: 10 → 25 credits (covers one 23-cr template gen).
- Packs: `pro_pack_50` $5.99/50, `pro_pack_120` $15.99/**150** (SKU name retains "120"; ASC display name must read "150 Credits"), `pro_pack_250` $24.99/250.
- Per-credit: $0.1198 / $0.1066 / $0.0999 — top pack reclaims BEST_VALUE badge (lowest per-credit).
- Per-pack margins at $1.32 COGS: 41% / 35% / 32%. Memory `project_monetization_model.md` rewritten for V2.0.0.

**Audio control flipped to per-template.** `template.audio_enabled` schema field added; `_dispatch_motion_transfer` reads it; `scripts/set_template_audio.py` CLI mirrors `set_template_hero.py`. Spike scripts default silent with a `--keep-audio` flag for explicit audio testing. Memory `project_kling_audio_test_policy.md` rewritten. NOW.md open question #7 resolved.

**App icon + splash rebranded to AIVO.** Locked design: minimalist Bodoni 72 Bold lowercase "a" with a single white dot above, on solid black (icon) / `#1C1614` (splash). Both 1024×1024, no alpha. Files dropped in `mobile/assets/images/icon.png` + `splash-icon.png`. Three earlier directions (wordmark + cyan star, big "a" + red star + trail variants, big "a" + light blue star) were explored and rejected in favor of minimalism. Memory `feedback_pillow_tittle_positioning.md` saved from the design iterations.

**`app.json`:** `name` → "AIVO", `version` → "2.0.0". buildNumber stays at 14; EAS auto-increments on next build.

**Committed + pushed** the bulk of session work (commit `0b1ba96` — V2 hero templates + preview_video + indicator pills) earlier in session. Subsequent changes (audio_enabled schema, pricing changes, icon assets, app.json rename) still uncommitted.

## Next step — Session 68 (on resume)

**Ship V2.0.0 to TestFlight.** Sequence:

1. Commit the uncommitted bundle: app icon + splash, app.json rename + version bump, audio_enabled schema + dispatcher, scripts/set_template_audio.py, BEST_VALUE_PACK flip, PACK_CREDITS pro_pack_120=150, _ANON_STARTER_CREDITS=25, Memory updates.
2. `npx expo prebuild --platform ios` (required after app.json name/version changes per `Memory/feedback_app_json_needs_prebuild.md`).
3. Decide audio_enabled per template — most likely Bombale/Gangsta/Baby Dance all want audio on for the dance music. Flip each via `scripts/set_template_audio.py --template-id ... --enable`. If audio flips on, **re-render preview_video.mp4 with audio on** so the carousel autoplay has sound (current previews are silent).
4. ASC manual steps (do BEFORE submitting the build): update IAP prices ($5.99 / $15.99 / $24.99), rename `pro_pack_120` IAP display to "150 Credits", change App Name to "AIVO", capture fresh screenshots from the V2 home with `xcrun simctl io booted screenshot`, verify privacy nutrition label includes "Photos" data type, iPad sim smoke pass.
5. `eas build --platform ios --no-wait` → TestFlight → ASC submit for review.

## Open questions

Top open items — Linear/AIV tracked items omitted unless load-bearing for the immediate next session.

1. **(High) Audio decisions per launch template.** Bombale/Gangsta/Baby Dance all `audio_enabled=None` (silent) right now. Dance trends almost certainly want audio on. Decide, flip, re-render previews.
2. **(High) Fresh ASC screenshots.** V2 home is dramatically different from V1 build #14 — different layout, hero pager, no tabs. Old screenshots will mislead reviewers. Capture native at 6.7" + 6.1" minimum.
3. **(Medium) Re-render preview_video.mp4 with audio on.** If audio_enabled flips to true on a template, the existing silent preview will be inconsistent with the runtime output. Re-running each chain script with `--keep-audio` produces the audio-on preview. Same upload path applies.
4. **(Medium) ASC App Name rename impact.** "Speech to Video" → "AIVO" might trigger Apple's "Name change" review path. Verify no extra paperwork required before submission.
5. **(Medium) iPad sim pass.** Per `Memory/reference_supports_tablet_false_does_not_block_ipad.md`, reviewers can still pick iPad. Smoke test before submit.
6. **(Medium) Privacy nutrition label review.** Selfie upload is new since V1 build #14 — confirm "Photos" data type is listed in ASC privacy section.
7. **(Medium) Bombale published-status drift** (S64 carryover) — once flipped from `published` to `draft` between S63 close and S64 start; cause still unknown.
8. **(Low) Coherence prompt scope.** Bombale's `prompt_template` (generic coherence principle) carried over verbatim to Gangsta + Baby Dance and worked. After 3 templates, could lock as dispatcher-only and drop the per-doc duplication.
9. **(Low) Pattern smell on spike scripts.** Three nearly-identical `test_*_chain.py` + three nearly-identical `seed_*_template.py`. Generalize when template #4 lands.
10. **(Low) Adult-on-baby-dance preview** — preview shows original child stand-in; at runtime an adult selfie gets the child's dance motion. Possibly uncanny but probably fine; flag if user reports come in post-launch.
