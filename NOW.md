# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 52 — 2026-04-25/26 — main (closing)
**Status:** Reds #4 (UI polish) and #5 (App Store metadata) are DONE. V1 simplification (Hailuo-only, 10s-only, 10 cr/gen, 10-credit free tier) shipped end-to-end across backend, mobile, and CLAUDE.md. Build #10 with the badge fix is attached in ASC under iOS App Version 1.0; Pricing & Availability set with 133 countries (EU/EEA excluded for DSA avoidance). **One click away from "Add for Review."**

## What happened this session

- **Vision interview → CLAUDE.md fully rewritten.** 4-topic interview (target user, core promise, quality bar, pricing) ratified. Mission: "Turn a fleeting visual idea into a shareable 10-second clip, on phone, in under 5 minutes, with zero setup." Brand voice tagline: *"Your weirdest idea, made real in 5 minutes."* Under-promise principle: never claim faster than 5 min in user-facing copy (actual ~30-60s). Locked Session 52 — every product/pricing decision now starts from this section.
- **V1 simplification — Kling and 6s dropped.** Single-model + single-duration: `minimax/hailuo-2.3` × 10s only. Backend `CREDIT_COSTS = {("hailuo", 10): 10}`, `_ANON_STARTER_CREDITS = 10`. `generate_speech_to_video` now MiniMax-only path; explicit error if `MINIMAX_API_KEY` not set. Mobile `FALLBACK_COSTS` mirrored. Removed model + duration pickers from `app/(tabs)/index.tsx`. Pricing math validated: $0.50 COGS, $0.35/gen margin at $4.99 pack vs $0.18 at $19.99 (top-pack discount eats margin — accepted for V1). Full repo sweep for stale Kling references (legal.py × 3, server.py, video_service.py).
- **Red #4 — UI polish: SHIPPED.** Speech-first restructure on Speech tab: large blue 130×130 mic button ABOVE text input. Recording state = red capsule with "Stop Recording" white text inside. Generate Video = blue capsule (h64, br32), white fontSize 24. Gallery: model/duration subtitles removed; cards re-aspected to 2:3 (cardWidth × 1.5); video player full-bleed; download/save UX cleaned. Settings: rebranded "AI Speech to Video v1.0.0". ConfirmModal: enlarged max-w-lg, p-6, Confirm button rewritten as direct Pressable to guarantee white text on blue. NetworkBanner: pushed below notch via `useSafeAreaInsets`. Gear icon added to Gallery header → Settings. Paywall: Best Value badge moved to actually-best `pro_pack_250`; `DEFAULT_SELECTED_PACK = pro_pack_120` keeps mid-pack as soft default. Font swap `font-heading` → `font-body-medium` for visual consistency.
- **Red #5 — App Store metadata: DONE in ASC.** App name: "AI Speech to Video". Full description, keywords, support URL (https://speech-2-video.ai/support — new `/support` endpoint added to legal.py with FAQ since `mailto:` is rejected by ASC), copyright, age rating, App Privacy questionnaire, App Review notes (no demo account needed; anon flow + 10 starter credits). 3 IAPs attached. Routing app coverage / App Clip / iMessage all skipped. Pricing & Availability: 133 countries selected, EU/EEA deselected (DSA avoidance per ToDo #24).
- **Build #10 shipped + attached.** First EAS build went out before the Best Value badge fix; queued a second build (autoIncrement → 10) with the fix. `eas submit` ran; build processed in TestFlight; selected in "1.0 Prepare for Submission" → Build section. Screenshots captured at iPhone 17 Pro Max native 1320×2868 via `xcrun simctl io booted screenshot` and dragged into ASC.
- **5 new lessons memorialized.** `feedback_sequence_ui_dependent_steps_after_polish` (do screenshots/UI-copy AFTER polish, not before). `feedback_verify_state_before_recommending_values` (always one-step verify version/URL/path before suggesting). `feedback_save_memory_only_after_verification` (don't memorialize speculative fixes). `reference_pressable_function_style_with_nativewind` (function-form `style={({pressed})=>...}` silently drops with NativeWind — use plain object). `reference_revenuecat_project_structure` + `reference_asc_iap_screenshots` (carried from S51).
- **Sim/Firestore quirks resolved.** `simctl uninstall booted` doesn't wipe Keychain; `simctl erase booted` is also unreliable in some flows. Recovery path when stuck at 0 credits: edit Firestore `credits/{uid}` doc directly OR delete both Firestore + Authentication entries to let `ensure_anon_starter` recreate cleanly. Memory `reference_simulator_keychain_persists.md` updated with S52 finding.

## Next step — Session 53 (on resume)

**Single click away from submitting to Apple App Review.**

1. Open ASC → App → Distribution → "1.0 Prepare for Submission".
2. Final pre-submit scan: confirm no red warning triangles in any sidebar section (App Information, App Review, App Privacy, App Accessibility, Pricing). Build #10 should still show attached with version 1.0.0.
3. Click **"Add for Review"** (top right). Confirm export compliance prompt if it appears (`ITSAppUsesNonExemptEncryption: false` is already in app.json so this should auto-confirm).
4. Submit. Watch for "Waiting for Review" status. Apple typically responds within 24-48h on first submission.

If anything looks off in #2 (e.g. App Privacy was reset, screenshots missing on a device size we didn't capture for), fix that one item then resubmit. Otherwise this is one click.

## Open questions (carryover + new)

- **(S52 new) First Apple review verdict.** No way to predict — could be approved, could be rejected with a 4.x or 5.x citation. If rejected, common landmines for our shape: 4.3a (spam/template), 5.1.1(v) (account deletion proof — already have a video-walkable flow), 2.1 (crashes on reviewer device — TestFlight on physical device would surface this; we shipped without).
- **(S52 carryover from #6)** TestFlight smoke test on a physical device never happened. We bet that iOS sim + EAS build is sufficient. If Apple rejects on a device-specific issue, this becomes the obvious next step.
- **(S48 follow-up B, still open) UX hole: home button shows cost not balance.** Generate button shows action label only ("Generate Video"). Balance is only visible in Settings. Decision needed post-launch: chip above button, badge on gear icon, or status pill in tab bar.
- **(ToDo #1, S50 origin)** Server-side TOCTOU credit gate. Client mitigation shipped, server still vulnerable to concurrent submits. Yellow — should land before any wider TestFlight release.
- **Backend Apple precheck + clip-merge** — Yellow #10. Haven't verified `/api/auth/apple/precheck` + `/api/clips/merge` exist in `server.py`. Clip-orphan risk on anon→Apple collision.
- **(S43-era, future trigger)** RC `default` offering "Current" is implicit today. The day a second offering is added, if `Purchases.getOfferings().current` returns `null`, check the RC dashboard for an explicit "Current" toggle.
- **(ToDo #10, post-launch)** Gallery cards still use prompt text + play icon — no image thumbnails. Reasonable V2 polish item.
