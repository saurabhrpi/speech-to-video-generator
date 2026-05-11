# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 61 — 2026-05-09 / 2026-05-10 — branch `v2`

**Status:** Backend Track 1 progressing — AIV-12 (R2 wiring) and AIV-13 (first-frame ffmpeg) both shipped and marked Done. DNS migration GoDaddy → Cloudflare completed cleanly (no API or email downtime). `assets.speech-2-video.ai` is Active with CF edge caching. R2 is ready for Track 2 asset gen. Three follow-ups filed. Large dirty tree — to be committed S62.

## What happened this session

- **Linear team prefix renamed SPE → AIV.** User changed it in Linear UI; I swept the codebase (`NOW.md`, `template_registry.py`, `seed_template_registry.py`, `feedback_lock_then_track.md`). Stale `SPE-NN` text inside Linear issue bodies is being cleaned **opportunistically** as we touch each issue (not bulk-rewriting — round-trip risk on inline `<issue id="…">` markup + operational risk of mass writes). Linear's `save_issue` auto-resolves plain `AIV-NN` tokens, so opportunistic edits land cleanly.
- **AIV-13 (first-frame ffmpeg) — DONE.** Added `extract_first_frame(video_path_or_url, out_path, thumbnail_size=None)` to `src/speech_to_video/utils/video.py`. Local + URL inputs, optional thumbnail resize, raises `RuntimeError` on ffmpeg failure. Smoke test `scripts/test_extract_first_frame.py` exercises 3 cases (local file, URL via in-process `http.server`, thumbnail). Initially marked Blocked on AIV-12 for the R2-URL acceptance bullet; re-tested against the real R2 URL after AIV-12 went live — PNG dimensions match source.
- **AIV-12 (Cloudflare R2 wiring) — DONE.** End-to-end.
  - **Code:** `boto3>=1.34` in `requirements.txt`. 5 R2_* settings in `utils/config.py`. New `src/speech_to_video/utils/r2_client.py` with lazy boto3 client + `upload_file` / `public_url` / `head_object` / `delete_object` + `R2NotConfigured`. Smoke test `scripts/test_r2_client.py` (5/5 green).
  - **DNS migration GoDaddy → Cloudflare** (locked Option A — full DNS host move):
    - TTLs lowered to 600s on all 16 records; 6h aging window observed
    - All 16 records mirrored at CF (1 A, 1 MX, 4 TXT, 8 CNAMEs, 2 SRVs); all proxiable records set to "DNS only" (gray cloud) — critical for Replit SSL + MS365 Exchange
    - NS flipped at GoDaddy 2026-05-10 12:48 PM CDT → `ajay.ns.cloudflare.com` / `ximena.ns.cloudflare.com`
    - CF activation confirmed via dashboard email + `dig @8.8.8.8`
    - Live API stayed up; MS365 email verified by real send/receive at `support@speech-2-video.ai`
  - **R2 setup:** bucket `speech-to-video-templates`, Account API token (Object R/W, bucket-scoped), custom domain `assets.speech-2-video.ai` bound + Active, Cache Rule `Cache R2 assets` deployed (hostname-equals → Eligible for cache + Edge TTL: use cache-control header). `CF-Cache-Status: HIT` verified on second fetch.
- **3 follow-up AIVs filed** (all Backlog):
  - **AIV-86** — Configure MS365 DKIM (Low, Launch Prep). No DKIM CNAMEs today; outbound mail SPF-only.
  - **AIV-87** — Replace legacy `secureserver.net` SPF include with MS365 (Low, Launch Prep).
  - **AIV-88** — Bulk-upload script for Track 2 asset-gen pipeline (Medium, Track 2). Deferred from AIV-12; gated on AIV-84 user reference images.
- **`CLAUDE.md` ungitignored** at user request. Removed from `.gitignore`. Edits this session: Video Stitching section renamed to Video Utilities; `extract_first_frame()` + `R2 Client` entries added under Key Components; R2 env vars added under Configuration. File is now untracked, ready to stage in S62 commit.
- **3 reference memories added:**
  - `Memory/reference_linear_save_issue_autolinks_tokens.md` — Linear MCP auto-links plain `<PREFIX>-<N>` tokens in descriptions.
  - `Memory/reference_cf_r2_token_screen_no_account_id.md` — R2 token result screen shows only 3 credentials; Account ID is on Account Home sidebar or the S3 endpoint URL shown alongside.
  - `Memory/reference_cf_r2_custom_domain_needs_cache_rule.md` — Binding R2 to a CF custom domain does NOT auto-enable edge caching; need an explicit Cache Rule.

## Next step — Session 62 (on resume)

1. **Commit the large dirty tree from S61.** Suggested message: `"AIV-12 R2 + AIV-13 first-frame; DNS migration to Cloudflare"`. Files to stage (excluding `.env` which stays gitignored):
   - Modified: `.gitignore`, `CLAUDE.md` (new untracked, stage explicitly), `Memory/MEMORY.md`, `Memory/feedback_lock_then_track.md`, `NOW.md`, `requirements.txt`, `scripts/seed_template_registry.py`, `src/speech_to_video/utils/config.py`, `src/speech_to_video/utils/template_registry.py`, `src/speech_to_video/utils/video.py`
   - New: `Memory/reference_cf_r2_custom_domain_needs_cache_rule.md`, `Memory/reference_cf_r2_token_screen_no_account_id.md`, `Memory/reference_linear_save_issue_autolinks_tokens.md`, `scripts/test_extract_first_frame.py`, `scripts/test_r2_client.py`, `src/speech_to_video/utils/r2_client.py`
2. **Pick the next Track 1 backend AIV.** Recommended order (per S60 sprint plan, narrowed by what's now unblocked):
   - **AIV-77** (selfie storage policy, design-only) — fast, locks a decision so AIV-15 can move
   - **AIV-79** (Vertex AI auth on Replit) — manual GCP project + service account work
   - **AIV-11** (Vertex AI client) — code, depends on AIV-79
3. **Subsequent sprint** (after Sprint 1 design pieces): **AIV-76** (direct Kling client), **AIV-14** (dispatch), **AIV-83** (GET /api/templates endpoint), **AIV-82** (template publishing workflow), **AIV-15** (selfie upload endpoint), **AIV-16** (variance harness).

## Branch state at close

- On `v2`. HEAD `9d76055` ("V2 template registry" — last S60 push).
- **Working tree dirty (S61 work uncommitted, large batch):**
  - `M .env` (R2_* secrets — gitignored, will not commit)
  - `M .gitignore` (CLAUDE.md removed)
  - `M Memory/MEMORY.md` (3 new index entries)
  - `M Memory/feedback_lock_then_track.md` (SPE → AIV)
  - `M NOW.md` (this rewrite)
  - `M requirements.txt` (boto3>=1.34)
  - `M scripts/seed_template_registry.py` (SPE → AIV)
  - `M src/speech_to_video/utils/config.py` (5 R2_* settings)
  - `M src/speech_to_video/utils/template_registry.py` (SPE → AIV)
  - `M src/speech_to_video/utils/video.py` (extract_first_frame added)
  - `?? CLAUDE.md` (newly tracked; Video Utilities rename + extract_first_frame + R2 Client + R2 config edits)
  - `?? Memory/reference_cf_r2_custom_domain_needs_cache_rule.md`
  - `?? Memory/reference_cf_r2_token_screen_no_account_id.md`
  - `?? Memory/reference_linear_save_issue_autolinks_tokens.md`
  - `?? scripts/test_extract_first_frame.py`
  - `?? scripts/test_r2_client.py`
  - `?? src/speech_to_video/utils/r2_client.py`
- `main` at `6aa2c2b`. `hotfix-build14` at `a432301`.

## Open questions

### S61 new

- **(AIV-86 — Launch Prep / Low)** Configure MS365 DKIM. Outbound mail SPF-only today. Not a launch blocker; revisit if we start sending much product mail OR a deliverability complaint surfaces.
- **(AIV-87 — Launch Prep / Low)** Replace legacy `secureserver.net` SPF include with MS365. Low-impact spoofing surface.
- **(AIV-88 — Track 2 / Medium)** Bulk-upload script for asset-gen pipeline. Gated on AIV-84 user reference images.

### S60 — assumption-locked, awaiting validation (carried over, minus what closed this session)

- **(S60)** AIV-10, AIV-14, AIV-15, AIV-26–29, AIV-35–37 — all carry "ASSUMPTION LOCKED" / "OPTIONS LOCKED" remarks. (AIV-12 and AIV-13 removed — Done S61.) Per `Memory/feedback_lock_then_track.md`: do NOT pre-emptively close.

### S60 — friend's dad

- **(S60 — friend's dad)** Awaiting his pick on company name (proposed: Lumara Studios / Cinder Apps / Reelform / Vimara / Frameloop) + structure choice (Pvt Ltd vs LLP vs OPC).

### S60 — AIV-84

- **(AIV-84 #1 — TACTICAL/BLOCKING for Track 2)** User to provide reference images for all 25 launch templates. Without these, per-template prompt drafting is guess-and-check and Track 2 asset gen (incl. AIV-88) is gated. Drop into chat or `docs/research/template_refs/`.

### S59 carryover — STILL OPEN

- **(S58 / AIV-49)** First organic Apple IAP purchase. Sandbox/TestFlight validated; production grant path untested. Watch RC dashboard + backend logs on first organic transaction.
- **(S53)** Dad's Apple Developer enrollment retry from home WiFi. Tracked in separate `Mom_Apple_Setup` Linear project.
- **(S53 / separate)** M365/Entra tenant decision. Covered in another Linear project per user direction.
- **(AIV-50)** UX hole: home button shows action label only, balance only in Settings. V2 home redesign (AIV-30) likely obviates.
- **(AIV-51 / ToDo #19)** CustomerInfo listener for offline-replay + RC ingestion-lag.
- **(AIV-52 / ToDo #27)** Verify concurrent-submit credit gate post-deploy.
- **(AIV-53 / Yellow #10)** Backend Apple precheck + clip-merge — verify endpoints exist in `server.py`.
- **(AIV-54)** RC `default` offering "Current" implicit — flag if 2nd offering arrives. Triggered by AIV-37 V2 IAP creation.

### S59 deferred

- **(AIV-38)** App rename — end-of-V2-build, display-name only.
- **(AIV-39)** (j) Product Showcase + (p) Text to video disposition — defer to end.
- **(AIV-40)** Pipeline B I2V cost-optimization spike (Hailuo I2V vs Kling 2.1 standard) — post-launch margin lever.
