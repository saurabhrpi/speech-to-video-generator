# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 86 — 2026-05-30 — branch `v2`

**Status:** V2.0.1 — functional blockers closed. **AIV-96 fixed + Done**, hero "Try It"/non-tappable shipped, **legal pages rewritten + deployed LIVE + verified**, **onboarding redesigned** (cycling before→after) and **hero carousel grown 3→7** (live data). What remains before release is the **ship sequence** (EAS build → submit) plus the **one hard gate: per-asset IP/likeness audit**. V2.0.0 is already public, so this is an update, not a first launch.

## What happened this session

- **AIV-96 (photo-permission dead-end) — root-caused + fixed + Done.** The `requestMediaLibraryPermissionsAsync()` gate was self-imposed; `launchImageLibraryAsync` needs NO photo-library permission on iOS (verified in expo-image-picker v17 native source). Removed the gate. Verified on sim across denied/undetermined/granted (forced via `simctl privacy`) — picker always opens. Linear AIV-96 → Done.
- **Hero carousel cards non-tappable + "Try It" pill** (bottom-right) — accidental taps no longer navigate; flow-layout overlay + `box-none` to dodge expo-av touch-swallow. Verified on sim.
- **Legal docs rewritten + LIVE.** Big discovery: live `/privacy` `/terms` `/support` are served by **our FastAPI backend** (`src/speech_to_video/api/legal.py`), **NOT Firebase Hosting** — S85 misread the "Google Frontend" header (= Replit's GCP fronting). Rewrote `legal.py` to the current stack: AIVO branding; **fixed the now-false "we retain your photo" → "deleted within 24h"**; added Google NBP, a China cross-border-transfer section, and a CCPA section; 18+ (was under-13); kept in-app Delete Account + TN/Davidson County venue. Operator = **Saurabh Sharma (individual)**, **Tennessee** law, **18+**. Backend redeployed (by user) → **verified live** (all new strings present, stale ones gone). Onboarding gate now links **both** Terms + Privacy; **consent key bumped v2→v3** (re-prompts every existing user once).
- **Onboarding redesign** (ref `~/Downloads/Onboarding.png`): cycles 3 dance videos on loop (Bombale/Gangsta/Mapopo) + circular **"Before"** NBP solo-selfie (frame 0 → NBP regen → phone removed → square face-crop, bundled) + curved arrow + template caption + "Welcome to AIVO" + tagline; heavy bottom band → smooth fade. JS-only (no native deps). **Fixed two bugs:** consent gate won't re-show on reload once v3 set (cleared the sim manifest key to force it), and the empty "Before" circle was a Fabric `absoluteFill`-in-rounded-wrapper bug (fix: size the `<Image>` directly).
- **Hero carousel 3→7** — promoted Soda Pop Energy, Copacabana, No Batidão, Mapopo to `is_hero` (order 3–6) via `set_template_hero.py`. **Live in Firestore** (server-driven → affects all users immediately, independent of the build).

## Next step — Session 87

1. **Commit the onboarding batch** (still UNCOMMITTED): `mobile/components/OnboardingScreen.tsx`, `mobile/assets/onboarding/{bombale,gangsta,mapopo}.jpg`+`arrow.png`+`bottom_fade.png`, scripts `gen_onboarding_before.py`/`nbp_edit_image.py`/`crop_face_square.py`/`gen_onboarding_chrome.py`. (Plus the held `NOW.md` + `ToDo.md` edits.)
2. **Resolve the IP/likeness gate** (Linear Urgent, "only hard pre-launch gate") — per-template clearance pass on the shipped catalog (dances/music/trademarks; hero slot most exposed).
3. **Ship sequence:** bump `mobile/app.json` version 2.0.0→2.0.1 → EAS production build (carries AIV-96 + hero + onboarding + consent v3) → device golden-path smoke test (1 real gen) → age-rating questionnaire (ASC, 18+) → EAS submit → TestFlight → review. Confirm ASC availability still excludes EU.

## Open questions

1. **(S86)** Per-asset **IP/likeness audit** — the one hard pre-launch gate (Linear Urgent). Scope into a per-template pass.
2. **(S86)** Bump marketing version `app.json` 2.0.0 → 2.0.1 before the build? (EAS owns buildNumber; version string is hand-set.)
3. **(S86)** Counsel once-over of the now-live legal docs (face uploads + China processors) before broad release.
4. **(S86)** Onboarding polish (optional): arrow position, 5s slide interval, crossfade vs instant swap. The "Open debugger to view warnings" banner is dev-only (gone in prod) — uninvestigated.
5. **(S86)** Linear hygiene: close issues already shipped (privacy rewrite, photo-consent UX AIV-42, credit-refresh AIV-97, home carousel redesign).
6. **(S85)** Age-rating questionnaire answers (ASC) for the 18+ content-maturity bump.
7. **(S85)** Admin R2 token created for the lifecycle apply can be **revoked now** (job done); app stays on its object-scoped token.
8. **(S82→S86)** Sim/device golden-path gen still not spot-checked (17+ templates) — do during the EAS smoke test.
9. **(S83→AIV-105)** Audio-lead RUNTIME sync unverified for v2.6-std + raw-driver.
10. **(S84→AIV-110)** Cleanup `~/Downloads/` intermediates + stale R2 build artifacts (AIV-110); **(S79→AIV-109)** non-Kling motion-transfer competitor research; **(S77→AIV-107)** streaming-preview monitoring; **(S81)** hero freeze threshold 0.6 tune.
