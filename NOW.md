# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 63 — 2026-05-12 / 2026-05-13 — branch `v2`

**Status:** **V2 motion-transfer pipeline end-to-end-validated on simulator, blocked only on real assets.** Four AIVs closed (83 / 82 / 16 / 31) + AIV-30 shell shipped + verified on the sim. Full Pipeline A chain — Firebase auth → credit gate → R2 selfie upload → dispatcher → Kling — runs cleanly. Sim test terminated at Kling 1201 ("Video URL is invalid"), the expected stopping point because Bombale's `driving_video_url` is still `placeholder.example`. Code is done; only AIV-84 #1 (real reference assets) blocks a real generation.

## What happened this session

**Four AIVs closed:**

- **AIV-83 (`GET /api/templates`) — DONE.** Public, no-auth read endpoint. In-process cache (60s TTL, `threading.Lock` held through Firestore fetch). Weak ETag = sha256 prefix of sorted `id|updated_at`. `If-None-Match` → 304. No CDN cache, no pagination at launch. Smoke (`scripts/test_templates_endpoint.py`) covers 200+ETag, 304 on match, 200 on mismatch, 4 GETs within TTL → 1 `list_templates()` call. Seeds dedicated `smoketest-aiv-83-published`; Bombale (draft) untouched.

- **AIV-82 (template publishing workflow) — DONE.** New `template_status_log` Firestore collection: `{template_id, from_status, to_status, actor, uid, reason, ts}`. `set_status()` writes doc update + log entry in a single Firestore batch. `list_status_log(template_id=..., limit=100)` client-sorts when filtered by id (avoids composite index; realistic per-template count <50). CLI `scripts/set_template_status.py` is the new primary admin path (replaces Firebase Console edits, which bypass the audit log and are explicitly accepted as un-logged for V2 launch). Smoke (`scripts/test_template_status_log.py`) green 6/6.

- **AIV-16 (variance harness) — DONE.** `scripts/template_variance_harness.py` — N×N grid via `VideoService.generate_template_video()`. Outputs `manifest.json` + `index.html` (templates as columns, selfies as rows, embedded `<video controls>`, fail cells flagged). `--dry-run` copies `docs/research/Kling_MotionControl_Image_Output.mp4` per cell. Cost guard initially $1.00 → tuned to $5.00 same session so routine 1×3 / 1×5 / 2×3 QA runs don't trip it. Dispatcher errors return dict-shaped — render coerces via `str()`. Pipeline A and B real-gen acceptance deferred until Track 2 assets land.

- **AIV-31 (Pipeline Review screen) — DONE + sim-verified.** New route `mobile/app/template/[id].tsx`: preview (video for Pipeline A, image for Pipeline B, placeholder when URL contains `placeholder.example`), `expo-image-picker` (library only, OS square crop), rights-consent checkbox, cost line, Generate. On Generate: `(creditBalance - inFlightCost) >= cost` → `/api/upload/selfie` (multipart) → `gallery-store.startTemplateGeneration()` (new sibling action) → POST `/api/generate/template-video` → `router.replace('/(tabs)/gallery')`. Reuses `runPoll` and the full 402/429/temp-id/abort machinery. App.json: added `expo-image-picker` plugin + fixed `NSPhotoLibraryUsageDescription` (was reusing save-to-Roll text, would have failed App Review on read use).

**AIV-30 (V2 home shell) — shipped, partial.** Shell only: `mobile/store/template-store.ts` (ETag fetch + AsyncStorage persist), `mobile/app/home-v2.tsx` (hero placeholder + category rows + tiles + skeleton/empty/error states + profile-icon → gallery + floating Create button → S2V). `(tabs)/index.tsx` got a `__DEV__`-only "Preview V2 home →" link. Sim test confirmed empty state, populated state (after Bombale flipped published via AIV-82 CLI), and unpublish. Still deferred for full close: real thumbnails (AIV-84 #1), hero curation, tab-nav removal, latency UX.

**End-to-end simulator validation (S63 afternoon):**

After three Replit redeploys (initially stale, then missing R2 secrets, then missing Kling secrets), the full Pipeline A chain executed cleanly:

1. Firebase Bearer auth ✓
2. `/api/templates` served ✓ (initial 404 → redeploy fixed)
3. Tile tap → `/template/{id}` ✓
4. Photo library pick + square crop ✓
5. Rights consent ✓
6. Credit gate ✓ (with workaround for AIV-51 stale-balance)
7. `/api/upload/selfie` ✓ (after R2 deployment secrets added)
8. `/api/generate/template-video` → `job_id` ✓
9. Gallery in-flight card ✓
10. Dispatcher routed Pipeline A ✓
11. Selfie presigned for Kling ✓
12. Kling JWT auth ✓ (after Kling deployment secrets added)
13. Kling API submit ✓
14. Kling fetch driving URL → **400 / code 1201 "Video URL is invalid"** ← only failure, expected (Bombale placeholder URL)
15. Error propagated job_manager → polling → gallery alert ✓
16. Credits NOT consumed ✓ (server consumes only on success)

**Discoveries / gotchas:**

- **Replit Deployment Secrets are independent of Workspace Secrets and not auto-synced** (existing memory `reference_replit_workspace_vs_deployment_secrets.md`). Bit us twice this session: R2 + Kling env vars existed locally but not on the prod deployment. Three redeploys to chase down.
- **RC test-store ingestion delay (>7s) breaks the 7s grant-retry chain** (existing memory `reference_rc_test_store_rest_delay.md`). User bought `pro_pack_50`, RC delayed, mobile gave up, balance never refreshed. Workaround: manual Firestore `credits/{uid}.balance` edit + app force-restart. Real fix is **AIV-51 / ToDo #19** (CustomerInfo listener) — now a verified live gap, not theoretical.
- **`scripts/dev_grant_credits.py` created + gitignored** as a one-shot recovery tool for AIV-51 gap. Local-only, never pushed. Reaches `credit_store.grant()` directly with a `dev-recover-*` tx_id. Blast radius: anyone holding the local admin SDK json. Decision logged in chat — not memorized.
- **Plan-doc references override Linear "open questions."** Asked the user about V2 home S2V placement; he pointed out `docs/V2_motion_transfer_plan.md` locks the answer (no tabs + floating Create + profile-icon top-right). Considered memorializing but he flagged it as obvious — CLAUDE.md MUST be read, that's baseline behavior.
- **Cost-guard threshold $1 was poorly tuned** — tripped on the AIV-16 acceptance run itself (1×3 = $1.50). Raised to $5 same session so routine QA isn't blocked but a wrong-dir typo still halts.
- **`--dry-run` default for CLI verification** memorialized (`Memory/feedback_default_dry_run_when_verifying.md`) after I edited the harness's threshold and re-ran without `--dry-run`, accidentally exercising the real Kling path against placeholder URLs.

**Side fixes / tweaks:**

- CLAUDE.md trimmed 568 → 467 lines: dropped grep-recoverable manifest sections (API Endpoint Reference, file-tree, file-listing in Mobile Frontend Architecture). Preserved decision-context (Pipelines table, Vision blocks, Standards, Pitfalls, docs/ convention).
- `mobile/package.json` + `mobile/app.json` updated for `expo-image-picker` (native dep — requires `expo prebuild --platform ios && expo run:ios`).
- `app.json` `NSPhotoLibraryUsageDescription` fixed (was reusing the save-to-Roll text for the read-access prompt — App Review would have flagged).

## Branch state at close

- On `v2`. HEAD `bedb905` (AIV-31). Pushed.
- Working tree: NOW.md (about to commit at /close) + `.gitignore` (adds `scripts/dev_grant_credits.py`).
- `scripts/dev_grant_credits.py` exists locally, gitignored, not in repo history.
- Seven S63 commits: `14439f1` (AIV-83) → `211087b` (AIV-82) → `8e03191` (AIV-16) → `ba5f7ec` (AIV-16 fix) → `e154def` (memory) → `c738650` (AIV-30 shell) → `bedb905` (AIV-31).
- `main` at `6aa2c2b`. `hotfix-build14` at `a432301`.

## Next step — Session 64 (on resume)

Working tree is essentially clean (only the close artifacts). The V2 motion-transfer code path is fully validated; what's left is content + remaining mobile polish + prod hardening.

Highest-leverage pickups (pick one):

1. **AIV-84 #1 — real reference assets for launch templates.** This is the hard gate. With it, the full V2 chain produces real output; without it, every Pipeline A/B run dies at Kling URL validation. User-action — depends on Saurabh kicking off the asset-gen pipeline (which itself needs `scripts/` extension per AIV-88 / "bulk-upload script").
2. **AIV-51 / ToDo #19 — CustomerInfo listener for RC offline-replay + ingestion-lag.** Now a verified live gap, not theoretical. Would have un-stuck S63 testing automatically.
3. **AIV-78 / 80 / 81 — production hardening.** Job manager durability (in-memory + 1h TTL — 7-min Pipeline B jobs die on restart), Replit thread verification, per-UID spend cap.
4. **AIV-30 remaining items** — tab-nav removal (V2 plan calls for it), real thumbnails (gated on #1), hero curation. Mobile.
5. **V2 gallery card variant** — in-flight + completed template-video jobs render via V1's S2V card today. Workable but not ideal.

User-action items waiting (AIV-84):
- #1: per-template visual references (gates Track 2 prompt drafting + V2 launch demo)
- #2: Nano Banana Pro allowlist request to Google (Vertex AI)
- #3: provide selfie+scene to finish AIV-11 Edit smoke
- #4: R2 lifecycle rules for `selfies/` + `composites/` prefixes (30d) in CF dashboard

## Open questions

### S63 new

- **(AIV-51 — Urgent)** Now a verified live gap. RC test-store ingestion >7s exceeds mobile's 7s grant-retry window; no auto-recover path; users see red "credits should appear shortly" + balance never refreshes. Workaround documented (manual Firestore edit + app force-restart). Fix: CustomerInfo listener that retries grant on app foreground + after ingestion settles.
- **(V2 home polish gap)** When V2 home replaces V1 home (tab-nav removal), the `__DEV__` "Preview V2 home →" link in `(tabs)/index.tsx` goes away. Until then, V1 is intact and V2 is reachable via the dev link.
- **(Deployment env-var checklist)** Three redeploys in S63 (initial stale, then R2, then Kling) because Workspace Secrets ≠ Deployment Secrets and we keep discovering them in production. `/api/setup` reports presence flags — could extend to mark MISSING-but-REQUIRED for current features. Not actioned this session.

### S62 carryover (still open)

- **(AIV-11 quality)** GA `gemini-2.5-flash-image` defaults to illustrative output even with photorealism prompt. Acceptable as launch fallback if Edit smoke (AIV-84 #3) shows usable composites; otherwise hard-block on Pro allowlist (AIV-84 #2).
- **(AIV-90)** Veo's V2 role still TBD. Schedule the client only if a real template needs it.
- **(AIV-14 latency)** Kling Motion Control image-mode ~6 min. V2 mobile UX needs expectation-setting + push-notification flow (AIV-44).

### S61 carryover (still open)

- **(AIV-86 — Launch Prep / Low)** Configure MS365 DKIM. Outbound mail SPF-only today.
- **(AIV-87 — Launch Prep / Low)** Replace legacy `secureserver.net` SPF include with MS365.
- **(AIV-88 — Track 2 / Medium)** Bulk-upload script for asset-gen pipeline. Gated on AIV-84 #1.

### S60 assumption-locked, awaiting validation

- AIV-26–29 + AIV-35–37 carry "ASSUMPTION LOCKED" / "OPTIONS LOCKED" remarks. Per `Memory/feedback_lock_then_track.md`: do NOT pre-emptively close.

### S60 friend's dad

- Awaiting his pick on company name (proposed: Lumara Studios / Cinder Apps / Reelform / Vimara / Frameloop) + structure choice (Pvt Ltd / LLP / OPC).

### S59 carryover

- **(S58 / AIV-49)** First organic Apple IAP purchase. Sandbox/TestFlight validated; production grant path untested.
- **(S53)** Dad's Apple Developer enrollment retry from home WiFi. Separate `Mom_Apple_Setup` Linear project.
- **(S53 / separate)** M365/Entra tenant decision.
- **(AIV-50)** UX hole: home button shows action label only, balance only in Settings. V2 home redesign (AIV-30) likely obviates.
- **(AIV-51 / ToDo #19)** **NOW VERIFIED LIVE GAP** — see S63 new above.
- **(AIV-52 / ToDo #27)** Verify concurrent-submit credit gate post-deploy.
- **(AIV-53 / Yellow #10)** Backend Apple precheck + clip-merge — verify endpoints in `server.py`.
- **(AIV-54)** RC `default` offering "Current" implicit — flag if 2nd offering arrives.

### S59 deferred

- **(AIV-38)** App rename — end-of-V2-build, display-name only.
- **(AIV-39)** (j) Product Showcase + (p) Text to video — defer to end.
- **(AIV-40)** Pipeline B I2V cost-optimization spike (Hailuo I2V vs Kling 2.1 standard) — post-launch margin lever.
