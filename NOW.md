# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 72 — 2026-05-21/22 — branch `v2`

**Status:** Smooth Criminal SHIPPED as the 3rd MJ Dances template (Beat It + Bad + Smooth Criminal now PUBLISHED under `mj_dances`). KlingMotionClient default bumped to `kling-v3` (Kling 3.0) for facial-consistency wins, with revert path documented — v3 costs ~2× v2.6 at the Kling-side API level, so the bump is on probation. CLAUDE.md + `kling_motion_client.py` docstring drift on `character_orientation` modes corrected. Higgsfield's ULTRA plan does NOT expose Kling 3.0 Motion Control programmatically (UI-only). Thriller chain in-flight: NBP edit perfected (1024×1024 1:1 via wide-arms T-pose prompt), final Kling run hung at Kling backend, no credits charged per user's Kling-console check — to recheck next session.

## What happened this session

**Smooth Criminal end-to-end.** Source 576×1024 → Replicate FHD upscale (247s) → R2 (canonical key) + CF purge. NBP holistic-regen on the cropped PNG; user iterated wardrobe (dark→beige top; original dark navy shorts + white sneakers kept; scene = patio with small tree + rolling hill + golden-hour light); X overlay self-removed on the beige re-run. Kling chain (v2.6 + pro + image + 10s + `--keep-audio`) → 1456×1424 (~1:1), 9.87s, 37MB, audio preserved. User renamed to `smooth_criminal_chain_final.mp4`. Uploaded as `preview_video.mp4`. Seeded `viral-dances-smooth-criminal` (mj_dances, 25 credits, `audio_enabled=True`) and flipped to published per S72 — runtime path inherits Beat It + Bad verification.

**Higgsfield investigation.** User asserted Higgsfield's web UI ships "Kling 3.0 Motion Control" with 3-30s driving video + character image; wanted to know if ULTRA plan exposes it programmatically. Installed Higgsfield CLI + MCP skills (`@higgsfield/cli`, `npx skills add higgsfield-ai/skills`), user OAuth'd. **Conclusion:** Higgsfield's `kling3_0` model_id accepts only `start_image`/`end_image` (I2V) — NOT motion-control. CLI's full server-side model list (11 video models) confirms NO `kling3_0_motion_control` variant. Plans (PLUS + ULTRA) say "Access to all models" — plans gate credits/rate/parallel, NOT endpoints. So upgrading would NOT unlock new model_ids. The UI feature is UI-only; likely Higgsfield calls Kling's direct API server-side with their own auth. Going direct with Kling stays the only programmatic path. (Memory: `reference_higgsfield_kling3_mc_ui_only.md`)

**Kling v3.0 evaluated on direct API.** Kling DOES have v3 on `/v1/videos/motion-control` — same endpoint shape we already call. Correct `model_name` string is **`kling-v3`** (NOT `kling-v3-0` — that returns error 1201 despite multiple wrapper docs claiming it). v3 wins: "upgraded motion capture + high facial consistency." **Cost surprise:** v3 ~2× v2.6 at the Kling level — v2.6 pro+image+10s = ~$1.02 Kling-side; v3 std+video+15s = ~$2.00 Kling-side. Bumped client default `kling-v2-6` → `kling-v3` at `kling_motion_client.py:72, 148` with explicit revert-path note in the class docstring. Single-line revert if v3 quality lift doesn't justify 2× cost on real-user data. (Memory: `reference_kling_v3_model_string_and_cost.md`)

**CLAUDE.md + client docstring drift on `character_orientation` corrected.** User push-back: "Pipeline B that you're referring to doesn't actually do what it appears to be doing — that's why we use NBP." Verified against `Memory/feedback_provider_mode_names_neq_outcomes.md` (S58 empirical): BOTH `image` and `video` modes produce Outcome 2 (motion-onto-character) on their own; Pipeline B's Outcome-1 result comes from the NBP composite pre-step, NOT from Kling's `video` mode in isolation. Fixed CLAUDE.md:256-258 bullet list, `kling_motion_client.py` submit() docstring, and the stale inline comment at `video_service.py:1129` ("Outcome 1: character-into-scene" → "I2V step on NBP-composited image").

**Thriller chain — aspect-ratio rabbit hole then breakthrough.** Original Thriller_5sec_onwards.mp4 (60s) cropped to 15s (5-20s). v3+std+video+15s output = 784×1168 (9:13.5 portrait); lateral gestures clipped per user. Five hypothesis attempts each iteratively failed:
- v3 + std + image + 10s → still 784×1168 portrait (hypothesis: image-orientation gives wider aspect — wrong)
- v3 + pro + image + 10s → 1184×1760 (still portrait, just higher res — hypothesis: pro gives ~1:1 — wrong)
- v2.6 + std + video + 15s → 784×1168 (hypothesis: v2.6 always outputs ~1:1 per S58 — wrong)

**Real root cause:** Kling MC inherits the NBP edit's aspect ratio. Past Pipeline A templates were wide because NBP was fed the cropped PNG (~1:1). Today's Thriller used the uncropped original (portrait input → portrait NBP output 848×1264 → portrait Kling output). User's insight: "Ask NBP to regenerate with both arms wide AND visible — that way it should generate a square box'ed png." Wide-arms T-pose prompt produced **1024×1024 perfect 1:1 NBP edit**. Re-fired Kling v2.6+std+video+15s on the 1:1 NBP edit — **task hung at Kling backend** (task `886680218651066459`, no progress in 12+ min on a 4-6 min typical gen). User checked Kling console: no credits charged for the hung task. (Memory: `reference_kling_mc_aspect_inherits_nbp.md`, `reference_kling_task_hang_detection.md`)

**Cost mistake — caught + corrected.** I quoted "~22-25 cr/gen" from `docs/V2_motion_transfer_plan.md` as the "historical Kling cost," but those are our RETAIL credits to users (COGS × 2), NOT Kling-side. User caught the conflation. Real Kling-side: v2.6 pro+image+10s = ~$1.12 COGS per doc (~$1.02 Kling + ~$0.10 NBP); v3 std+video+15s = ~$2.20 COGS today (~$2.00 Kling + ~$0.20 NBP). Lesson: when user asks "what did Kling charge us," answer in Kling's units/$, not retail credits.

## Kling elapsed-time data (S72 sample, for reference)

Small sample; wall-clock variance dominates at this volume. No reliable "v3 faster than v2.6" pattern in this session's data.

| Run | Elapsed |
|---|---|
| Smooth Criminal — v2.6 + pro + image + 10s | 5.4 min |
| Thriller — v3 + std + video + 15s | 5.4 min |
| Thriller — v3 + std + image + 10s | 4.2 min |
| Thriller — v3 + pro + image + 10s | 5.2 min |
| Thriller — v2.6 + std + video + 15s | **3.8 min** (fastest) |
| Thriller — v2.6 + std + video + 15s (re-run) | **hung** at 611s+ |

Averages: v3 (3 runs) = 4.9 min; v2.6 (2 successful, this session + Smooth Criminal) = 4.6 min.

## Thriller-completion checklist (S73 pick-up)

- [ ] Direct-poll Kling task `886680218651066459` (use the same one-liner pattern as in S72: `KlingMotionClient()._headers()` + GET `/v1/videos/motion-control/{task_id}`)
- [ ] If `task_status: succeed` — download `task_result.videos[0].url` → save as `~/Downloads/thriller_chain_final.mp4`
- [ ] If still hung → re-submit: `.venv/bin/python scripts/test_thriller_chain.py --edited-image "/Users/saurabhsmacbookair/Downloads/App Templates Prep/Working/thriller_edit_05a075bd.jpg" --keep-audio` (config: v2.6 + std + video + 15s + unletterboxed driving — all already in chain script + R2)
- [ ] **VERIFY ASPECT** — confirm Kling output is ~1:1 (e.g., 1024×1024 or 1456×1424 range). If yes → promote `Memory/reference_kling_mc_aspect_inherits_nbp.md` from PROVISIONAL to confirmed. If output is portrait (~9:13.5), the wide-arms T-pose recipe FAILED — revise/delete that memory and re-investigate.
- [ ] Crop final output to first 12s via ffmpeg (`-ss 0 -t 12`, libx264/aac re-encode) to drop the explicit content in the last 3s
- [ ] Stage cropped result as `~/Downloads/template_assets/viral-dances/thriller/preview_video.mp4`
- [ ] Upload via `.venv/bin/python scripts/upload_template_assets.py ~/Downloads/template_assets --template viral-dances-thriller --no-update-registry` (preview_video URL already published once; CF purge needed on overwrite)
- [ ] CF purge: `.venv/bin/python scripts/purge_cf_cache.py https://assets.speech-2-video.ai/viral-dances/thriller/preview_video.mp4`
- [ ] Write `scripts/seed_thriller_template.py` — copy `seed_smooth_criminal_template.py`, change: TEMPLATE_ID=`viral-dances-thriller`, title=`Thriller`, description=`Iconic zombie moves, sharp rhythms, midnight energy 🧟⚡` (or similar), category=`mj_dances`, credit_cost=25, audio_enabled=True, asset URLs to thriller paths
- [ ] Run seed: `.venv/bin/python scripts/seed_thriller_template.py`
- [ ] Flip published: `.venv/bin/python scripts/set_template_status.py viral-dances-thriller published --reason "S73 — 4th MJ dances template"`

## Next step — Session 73

**1. Resolve hung Thriller Kling task** — follow the Thriller-completion checklist above. No credits at risk per user's Kling-console check.

**2. Continue V2.1 template rollout (2 remaining):**
- **Pinky Up** — source already 1080×1920, no upscale. Use wide-arms T-pose NBP prompt to force ~1:1 from the start. S70 approved direction: pastel-pink hoodie + black biker shorts + white sneakers, pink-painted studio with soft neon accent.
- **Rasputin** — source already 1080×1920, no upscale. Same flow. S70 direction: black turtleneck + brown corduroy + boots, smoky lounge with red velvet drapes + warm chandelier.

**Tactical reminders:** per-template flow in `docs/V2_template_creation_runbook.md` — but two S72 amendments: (a) use wide-arms T-pose NBP framing to lock ~1:1 output aspect; (b) verify which Kling model the chain uses — client default is now `kling-v3` (~2× v2.6 cost). Pass `model_name="kling-v2-6"` explicitly in chain scripts if budget matters more than facial consistency.

**3. V2.0.1 ship work (carryover S71):**
- AIV-97 credit refresh on foreground (`AppState` listener + on-mount refetch)
- AIV-98 Show My ID in Settings (`auth().currentUser?.uid` + copy-to-clipboard)
- Revert AIV-94 temp UID-logging from `firebase_auth.py` (one-liner)
- Bump `mobile/app/settings.tsx` version label `v1.0.0` → `v2.0.1`
- Fix `CLAUDE.md` `_ANON_STARTER_CREDITS` constant drift (10 → 25)
- EAS build (autoIncrement to buildNumber 16) → TestFlight submit. Metadata-only ASC update sufficient.

## V2.0.2 production-resilience checklist (NEW S72)

Production handling for Kling hangs (today: 10-min timeout → generic error + no credits consumed). Not blocking V2.1; queue for V2.0.2.

- [ ] **Auto-retry once on Kling timeout** in `video_service.py` — credits not consumed on failure, so retry is free; user sees no friction, just delay
- [ ] **Friendly "still working" progress copy past 5 min** — e.g. "Our model is taking a bit longer than usual…"
- [ ] **Explicit apology copy on failure** with "Try again — no credits charged" CTA, not the current generic error

## Open questions

1. **(NEW S72)** Thriller hung Kling task `886680218651066459` — direct-poll status next session; resubmit if still hung. No credits at risk.
2. **(NEW S72)** Decide if Kling v3's facial-consistency lift justifies the ~2× cost vs v2.6. Pending real-user A/B data. Until then, the client default stays `kling-v3` with revert path documented at `kling_motion_client.py:72, 148` + class docstring.
3. **(Low, S71 carryover)** AIV-96 root cause unknown — why didn't iOS native permission sheet fire on dad's first photo-pick tap? Open Settings button is a band-aid. Add `perm.status` + `perm.canAskAgain` + `perm.accessPrivileges` logging.
4. **(Medium, S71 carryover)** AIV-99 slider-phone hero — when scheduled, pick path: (a) conditional z-index swap based on scrollY threshold, OR (b) gesture-handler + reanimated worklets custom scroll. Recommend (b).
5. **(Medium, S69 carryover)** RC Test Store prices stale for dev parity ($5.99 / $15.99 / $24.99 mismatched). Not blocking.
6. **(Medium, S64 carryover)** Bombale published-status drift spot-check. S71: driving video had drifted to 12.79s, cropped + CF-purged. Verify no further drift before V2.0.1 submit.
7. **(Low, S64 carryover)** Coherence prompt scope — with 6 published templates (Bombale + Gangsta + Baby Dance + Beat It + Bad + Smooth Criminal), consider locking as dispatcher-only and dropping per-doc duplication.
8. **(Low, S70)** Auto-bump `updated_at` on Firestore template writes (write-through hook in `template_registry.py`) so partial updates can't desync the `/api/templates` ETag.
9. **(Low, S70)** `scripts/upload_template_assets.py` only matches canonical basename slots. Worth extending the uploader or documenting `_manifest.json` escape in the runbook.
10. **(Low, S71)** AIV-95 Beat It output quality polish — re-do Beat It with cleaner-source approach (per S71 Bad lesson) post-V2.1 launch.
11. **(Low, S71)** Bad runtime production gen path: verified working for Beat It but not Bad. Sim-test on iPhone before any real-user gens hit it.
12. **(Low, S70)** Adult-on-baby-dance preview — preview shows the child stand-in; runtime applies child motion to adult selfie. Acceptable for V2.0 ship; revisit if user feedback flags it.
