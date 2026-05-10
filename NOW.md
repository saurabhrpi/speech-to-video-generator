# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 60 — 2026-05-08 / 2026-05-09 — branch `v2`

**Status:** V2 organized end-to-end in Linear. All planning blockers locked. Backend Track 1 kickoff: AIV-10 template registry implemented + verified live in Firestore. Working tree dirty with the registry code + 2 new feedback memories — to be committed next session.

## What happened this session

- **Linear MCP activated, V2 project organized.** Renamed "V2 : Replica of AI Video" → "V2 — Motion Transfer + Home Redesign". Created 4 milestones (Track 1 Backend, Track 2 Asset Gen, Track 3 Mobile UX, Launch Prep), 10 labels (pipeline-A/B, infra, template, mobile, legal, decision, risk, iap, v1-carryover), and ~75 issues (AIV-10–84).
- **All 25 V2 launch templates locked.**
  - 9 Pipeline A (Viral Dances) — AIV-17–25.
  - 16 Pipeline B (scene-insertion) picked from pools + drafted with scene concepts at AIV-60–75 (5 Trends, 4 Birthday, 4 Awards/Olympics, 3 Flying). The 4 pool-pick decision AIVs (AIV-26–29) carry the locked picks + skip reasoning.
- **Backend planning decisions all locked** (per new "lock-then-track" pattern — no Done until end-state; just status note "Only assumption confirmation pending"):
  - AIV-10 schema → Firestore, no versioning, English-only
  - AIV-12 R2 → public-read + custom domain `assets.speech-2-video.ai`
  - AIV-14 dispatch → **direct Kling API** (user override, NOT AIMLAPI). Vertex AI for Nano Banana Pro (Vertex isn't a middleman — IP indemnity matters).
  - AIV-15 endpoint → separate `POST /api/upload/selfie` (selfie reuse across gens)
  - AIV-35 anon credits → 25cr V2 starter
  - AIV-36 retail → unified 23cr per gen (both pipelines same retail)
  - AIV-37 IAPs → planned product IDs assumed (`credits_10/50/100/250`)
- **7 new backend gap AIVs created** (Track 1 / Launch Prep): AIV-76 direct Kling client, AIV-77 selfie storage policy, AIV-78 job manager durability, AIV-79 Vertex AI auth on Replit, AIV-80 Replit thread verification, AIV-81 per-UID spend cap, AIV-82 template publishing workflow, AIV-83 GET /api/templates endpoint.
- **AIV-7 moved** from Vanilla T2V project to V2 / Track 3 Mobile UX milestone (it's V2-relevant gallery UX, not V1-only). Vanilla T2V project is now empty.
- **AIV-84 "Tough but CRITICAL open problems"** created — living tracker for hard problems needing user input. First entry: user to provide reference images for all 25 launch templates (gates Track 2 asset gen meaningfully).
- **AIV-10 SHIPPED — first Track 1 deliverable.** Two new files:
  - `src/speech_to_video/utils/template_registry.py` (192 lines) — Firestore-backed registry with `get_template` / `list_templates` / `upsert_template` / `set_status` / `delete_template` / `_validate`. Schema constants (PIPELINE_*, OUTCOME_*, STATUS_*) match locked enums. Lazy-init Firestore client matching credit_store.py convention.
  - `scripts/seed_template_registry.py` — Bombale fixture seeder. Ran clean; user confirmed `templates/viral-dances-bombale` doc visible in Firestore.
- **Two new feedback memories saved** (still in working tree, untracked):
  - `Memory/feedback_lock_then_track.md` — at non-blocker decisions, lock with assumption + status note, do NOT mark Done until full implementation + validation; user phrased it: "we can't be blocked while the whole city is waiting to be built."
  - `Memory/feedback_direct_to_og_provider.md` — prefer direct API to OG provider (no wrappers like AIMLAPI). But verify what's actually a wrapper: Vertex AI is direct Google, not a middleman.
- **Side task — friend's dad's company.** Indian AI-video-app shop needs CPA paperwork. Proposed 5 brand names + detailed description covering provider-vs-developer classification, export-of-service status (Apple/Google as merchant of record), and software type detail per Indian GST/MCA expectations. Awaiting his pick.

## Next step — Session 61 (on resume)

1. **Commit the dirty tree** — registry module + seed script + 2 memories + MEMORY.md update. Single commit "Adding V2 template registry + S60 planning memories" or similar.
2. **Continue Sprint 1 backend** in dependency-friendly order:
   - **AIV-13** first-frame ffmpeg extraction (smallest, fully standalone, no external deps) ← recommended next
   - **AIV-77** selfie storage policy (design-only, lock the decision so AIV-15 can move)
   - **AIV-79** Vertex AI auth on Replit (manual GCP project + service account work)
   - **AIV-12** R2 wiring (manual Cloudflare account setup) — parallel-able with #79
3. **Sprint 2 (after Sprint 1's design pieces):** AIV-11 Vertex AI client, AIV-76 direct Kling client.
4. **Sprint 3:** AIV-14 dispatch, AIV-83 GET endpoint, AIV-82 publishing workflow.
5. **Sprint 4:** AIV-15 endpoint, AIV-16 variance harness.

## Branch state at close

- On `v2`. HEAD `3af5d6c` ("Adding docs, memories and test scripts" — last S58 push).
- **Working tree dirty (S60 work uncommitted, intentional — to be committed S61):**
  - `M Memory/MEMORY.md` (2 new index entries for the new feedback memories)
  - `?? Memory/feedback_lock_then_track.md` (new memory)
  - `?? Memory/feedback_direct_to_og_provider.md` (new memory)
  - `?? src/speech_to_video/utils/template_registry.py` (AIV-10 implementation)
  - `?? scripts/seed_template_registry.py` (Bombale fixture seeder)
- `main` at `6aa2c2b`. `hotfix-build14` at `a432301`.

## Open questions

### S60 new

- **(AIV-84 #1 — TACTICAL/BLOCKING for Track 2)** User to provide reference images for all 25 launch templates. Without these, per-template prompt drafting is guess-and-check and asset gen is much slower / more variance-prone. Drop into chat or `docs/research/template_refs/`.
- **(S60 — assumption-locked, awaiting validation)** AIV-10/12/14/15/26–29/35–37 — all carry "ASSUMPTION LOCKED" or "OPTIONS LOCKED" remarks. Status notes describe the trigger to close (downstream usage, post-launch data validation, etc.). Per `Memory/feedback_lock_then_track.md`: do NOT pre-emptively close.
- **(S60 — friend's dad)** Awaiting his pick on company name (proposed: Lumara Studios / Cinder Apps / Reelform / Vimara / Frameloop) + structure choice (Pvt Ltd vs LLP vs OPC).

### S59 carryover — STILL OPEN

- **(S58 / AIV-49)** First organic Apple IAP purchase. Sandbox/TestFlight validated; production grant path untested. Watch RC dashboard + backend logs on first organic transaction.
- **(S53)** Dad's Apple Developer enrollment retry from home WiFi. Tracked in separate `Mom_Apple_Setup` Linear project (NOT in V2 — different person/scope).
- **(S53 / AIV-X — separate)** M365/Entra tenant decision. User said "low-priority, skip" S60 — covered in another Linear project per their direction.
- **(AIV-50)** UX hole: home button shows action label only, balance only in Settings. V2 home redesign (AIV-30) likely obviates.
- **(AIV-51 / ToDo #19)** CustomerInfo listener for offline-replay + RC ingestion-lag.
- **(AIV-52 / ToDo #27)** Verify concurrent-submit credit gate post-deploy.
- **(AIV-53 / Yellow #10)** Backend Apple precheck + clip-merge — verify endpoints exist in `server.py`.
- **(AIV-54)** RC `default` offering "Current" implicit — flag if 2nd offering arrives. Triggered by AIV-37 V2 IAP creation.

### S59 deferred

- **(AIV-38)** App rename — end-of-V2-build, display-name only.
- **(AIV-39)** (j) Product Showcase + (p) Text to video disposition — defer to end.
- **(AIV-40)** Pipeline B I2V cost-optimization spike (Hailuo I2V vs Kling 2.1 standard) — post-launch margin lever.
