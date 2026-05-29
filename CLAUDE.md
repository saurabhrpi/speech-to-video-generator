# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current Focus (as of 2026-05-28)

**Shipping product:** Mobile AIVO motion-transfer template app (`mobile/`). Home is a template gallery — user taps a tiktok_dances tile → uploads a selfie → Pipeline A (Nano Banana Pro regen + Kling Motion Control) returns a dance clip to the gallery. Currently on **V2.0.1** (active dev on the `v2` git branch: home redesign, viewport-gated tile playback, first-frame posters, Coins UX rebrand, 45+ tiktok_dances templates) — heading for Build #15+. Entry point: `mobile/app/index.tsx` (home grid) → `mobile/app/template/[id].tsx` (selfie pick + Generate) → `POST /api/generate/template-video` → `video_service.generate_template_video` → Kling Motion Control client.

**Paused:**
- **Interior Timelapse pipeline** — Timelapse-Phase-2 target (NOT project-release V2). Backend code (`generate_timelapse_v2`, timelapse prompts, stitching) stays in the repo. Mobile has dormant wiring (`pipeline-store.ts`) but no active UI entry. Web has an active UI for it, but web itself is paused.
- **Web frontend** (`web/`) — future version TBD. Do not invest here unless asked.

**Rule for future sessions:** When product direction changes, update THIS Current Focus section in the same session. Don't let it rot. Every product/pricing/architecture decision must start from what's actually shipping (mobile), which means reading `mobile/app/index.tsx` (home grid) and `mobile/app/template/[id].tsx` (template detail) first, not the Vision sections below.

---

## Versioning convention (locked S59)

Project release names — used uniformly across docs, conversation, and commit messages:

- **V2** — the motion-transfer + template gallery app, AIVO branded. Currently on **V2.0.1** (active dev on the `v2` git branch: home redesign, viewport-gated tile playback, first-frame posters, Coins UX rebrand, 45+ tiktok_dances templates) — heading for Build #15+. Plan + scope: `docs/V2_motion_transfer_plan.md`. Template catalog: `docs/V2_template_catalog.md`. **NOT** the same as Timelapse-Phase-2 below. (Past + future release names tracked outside CLAUDE.md.)
- **Timelapse-Phase-2** — the second iteration of the (paused) Interior Timelapse pipeline. Internally referenced in code as `generate_timelapse_v2()` (function name unchanged). **Use "Timelapse-Phase-2" in docs/conversation** to disambiguate from project-release V2. Resumes if/when product direction returns to interior renovation timelapses.

When a section or comment uses bare "V2", it always refers to the project release (motion-transfer + home-screen). Never to Timelapse.

---

## Product Vision — Mobile Speech-to-Video (Shipping)

_Locked Session 52 (2026-04-24/25) via Vision interview. Single-model + single-duration simplification ratified Session 52 — Kling and Hailuo 6s dropped to maximize V1 simplicity. Update this block in the same session if product direction shifts._

**Mission.** Turn a fleeting visual idea into a shareable 10-second clip, on phone, in under 5 minutes, with zero setup. We win when impulse-to-output stays under 5 minutes and the output is recognizable enough to send to a friend without apologizing for the AI. (Actual gen time today is ~30-60s on Hailuo. We under-promise externally and over-deliver — never claim anything faster than 5 min in user-facing copy.)

**Target user.** Someone with a momentary creative impulse — a joke for a friend's birthday, a weird visual that popped into their head, B-roll filler for their personal Story. Mobile-only because the moment is mobile (walking the dog, in line, between meetings). Speech is a first-class input because they don't want to wrestle with prompt structure — they want to verbalize and go.

User mix:
- Primary: **self-expression** — output goes to a small social context (text a friend, group chat, personal IG/TikTok Story). Not for an audience, not for a client.
- Secondary (~15%): **casual creators** using AI clips as filler/B-roll for personal feeds.
- Tiny (~5%): **commercial slice** — paid-client folks making 10s commercial spots.

Engagement split (best guess pre-data): ~80% one-shot tourists (1-3 clips, share, never return), ~15-20% casual regulars (a few times a month).

**Competition.** We don't out-quality Sora / Runway / Pika / Veo — bigger models, more compute, deeper teams. We compete on **form factor and friction**: phone not web; one tap to first gen vs account + credit card upfront; speech vs typing; under 5 minutes vs longer + clunkier flows; camera roll + share sheet vs project dashboard. The realistic alternative we displace is **apathy + meme-reposting**, NOT the AI-video category leaders.

**Quality bar.** "Would I send this to a friend without apologizing for the AI?" Decomposed: subject recognizable, motion verb visible, no clip-killer artifacts (face glitch, missing limb, mid-clip freeze), full 10-second duration, crisp on a 6.7" phone screen at native scale.
- Hard fails (post-V2-launch detection target — see `ToDo.md` #22): completely abstract output, NSFW, watermarks, short clip, corrupted file, charged-but-timed-out.
- Soft fails (ship today): minor uncanny artifacts, missed prompt detail.

**Model + duration: single combination.** V1 ships one model, one duration:
- **Hailuo** (`minimax/hailuo-2.3`) via direct MiniMax API. User-facing promise: <5 min (actual ~30-60s — under-promise, over-deliver). Strong on cute animals + simple motion + surreal scenes — exactly the casual-impulse use case.
- **10-second clips only.** Long enough for a complete moment, short enough for share-friendly social formats.
- No model picker, no duration picker. Type/speak prompt → tap Generate → clip arrives. (Kling and Hailuo 6s were dropped Session 52 to maximize simplicity for V1; both can be re-added post-launch if data demands.)

**Brand voice.** Playful but reviewer-safe (Apple's reviewers are humorless; over-irreverence triggers 4.3a). Tonal anchor for App Store + paywall copy: *"Your weirdest idea, made real in 5 minutes."* Avoid corporate-speak ("AI-powered video generation platform") and pure-meme tone (curse words, dense irony). Under-promise principle: never claim faster than 5 min in user-facing copy, even though Hailuo typically returns in 30-60s.

**Pricing strategy** (Session 43 → Session 52 simplified to round numbers):
- **Per gen: 10 credits = $1.00 retail.**
- **Anon free tier: 10 credits = 1 free gen.** One-time, not refilling. Paywall on second gen attempt.
- **Three credit packs** (ASC IAPs already created):
  - `pro_pack_50` — $4.99 / 50 credits = **5 gens**
  - `pro_pack_120` — $9.99 / 120 credits = **12 gens** (BEST_VALUE)
  - `pro_pack_250` — $19.99 / 250 credits = **25 gens**
- ~$0.50 COGS/gen. After Apple's 15% Small Business cut: $0.35/gen margin at the $4.99 pack, $0.18/gen at $19.99 (bulk discount eats top-pack margin — accepted for V1; revisit when conversion data lands).

**No subscription at launch.** Adds reviewer surface area + churn UX + lapsed-user re-engagement work. Re-evaluate at month 3-6: if the 15-20% returning core spends >$9.99/mo on packs, sub becomes obvious; if not, credits stay.

**Factual context (carried from previous version):**
- Monetization model details: see `memory/project_monetization_model.md`.
- Auth: Firebase (anon + Apple Sign In). Paywall bundles sign-in, never standalone.
- Live cost math: `CREDIT_COSTS` in `src/speech_to_video/api/server.py`; mobile mirror in `mobile/lib/constants.ts:FALLBACK_COSTS`.
- AIMLAPI client (`clients/aimlapi_client.py`) stays in repo for paused Timelapse-Phase-2 work — unused by the shipping S2V path.

---

## Product Vision — Interior Timelapse (Paused — Timelapse-Phase-2 Target)

**Mission:** Automate the creation of hyper-realistic interior renovation timelapse videos (15-25 seconds) so that UGC makers can produce viral engagement content without a film crew.

**Target users:** Freelancers posting on TikTok/Instagram and marketing agencies working for interior designers and design companies. These users currently create renovation timelapses MANUALLY — the app replaces that entire manual workflow with automation.

**Origin:** The architecture is borrowed from a freelancer's course on making viral AI videos. The manual workflow: generate a "before" image with ChatGPT, iteratively renovate it 6-7 times using Nano Banana Pro (feeding previous image + edit prompt each time), feed the sorted images to Kling AI to generate transition videos between consecutive stages, add a final pan/explore shot, stitch everything. The result is mind-blowing. This app automates that exact workflow end-to-end.

**Core offering (when this was active):** The Interior Timelapse tab was intended as the core product, with Video Studio and Speech-to-Video as secondary/experimental. **This is no longer true** — the shipping product pivoted to mobile Speech-to-Video. Timelapse is being kept warm for Timelapse-Phase-2.

**Quality bar:** Output must be hyper-realistic — as if generated by a film crew using cameras on-site. Every technical decision (prompt engineering, model selection, architectural choices) serves THAT and ONLY THAT goal.

**UX philosophy:** Almost hands-off, one-click. User provides room type, style, and features (the 3 important inputs). Everything else should be automated.

**Model philosophy:** No attachment to any specific model. If something better than GPT, Nano Banana Pro, or Kling emerges tomorrow, switch immediately. Models are interchangeable tools in service of hyper-realism.

**Cost and speed:** Currently ~$7 per generation and ~20-25 minutes. Betting on model price drops and faster models for major cost/time reduction, and architectural changes for incremental improvements. No fixed strategy yet — figuring it out through trial and error.

**6-month goal:** $10K/month net profit after taxes.

## Known Problems — Timelapse-Phase-2 (Paused, but still relevant when work resumes)

These are frustrations from the Timelapse-Phase-1 era. They will matter again when Timelapse-Phase-2 work restarts; NOT active concerns for the shipping S2V product.

1. **Transition video quality is not good enough.** Even with Kling (the expensive model), weird artifacts appear: half a wall left unrenovated, vents/drains "blown through" walls during transitions. Hailuo (the cheap model) is completely hallucinated garbage with no coherence.

2. **Visual delta between stages is sometimes too small.** The difference between consecutive keyframe images can be barely noticeable, which makes for a bad viewing experience.

3. **Can't reliably handle more than 2 features.** Haven't experimented beyond 2 user features out of fear the app can't handle the complexity. Currently barely gets by with 2 features as desired.

4. **Prompt mismatch between indoor and outdoor spaces.** Prompts that work for closed rooms (bathroom, kitchen) don't transfer well to patios/outdoor spaces, and vice versa.

## Development Commands

### Python Backend

**Setup:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Run the FastAPI server:**
```powershell
python -m uvicorn src.speech_to_video.api.server:app --host 0.0.0.0 --port 5000
```

Or with auto-reload:
```powershell
python -m src.speech_to_video.api.server
# Uses environment variables: HOST (default 0.0.0.0), PORT (default 5000), RELOAD (default 0)
```

**Run the legacy Gradio UI:**
```powershell
python -m src.speech_to_video.webui.app
```

**CLI usage:**
```powershell
python -m src.speech_to_video.cli transcribe --audio path\to\audio.wav
python -m src.speech_to_video.cli generate --prompt "A serene beach" --duration 10 --quality high
python -m src.speech_to_video.cli speech-to-video --audio path\to\audio.wav --duration 60 --quality high
```

### Mobile (Expo / React Native) — SHIPPING FRONTEND

```bash
cd mobile
npm install
npx expo run:ios          # Dev client build on simulator (preferred — not expo start)
npx expo prebuild --platform ios   # Regenerate ios/ after app.json changes
```

Never use `npx expo start` — dev client keeps data safe from Expo Go resets (see `memory/feedback_expo_run_ios.md`). Mobile targets the FastAPI server via `API_BASE` env var. Builds and TestFlight submissions go through EAS.

### React Web Frontend (PAUSED — future version TBD)

```powershell
cd web
npm install
npm run dev      # Development server (Vite, port 5173)
npm run build    # Production build
npm run preview  # Preview production build
```

The web frontend proxies `/api/*` to `http://localhost:5000` in dev. In production, FastAPI serves React from `web/dist`. Not actively developed — kept for reference and possible future revival.

## Architecture

### Pipelines

| Pipeline | Frontend | Endpoint | Priority |
|----------|----------|----------|----------|
| **Speech-to-Video** (single T2V clip) | Mobile — `mobile/app/(tabs)/index.tsx` | `POST /api/generate/speech-to-video` | **SHIPPING — CORE PRODUCT** |
| **Transcribe audio → text** (pre-step for S2V) | Mobile — same screen | `POST /api/transcribe` | SHIPPING — supporting |
| **Interior Timelapse** | Web `timelapse` tab (paused) | `POST /api/generate/timelapse` | PAUSED — Timelapse-Phase-2 target |
| **Video Studio** | Web `video_studio` tab (paused) | `POST /api/generate/custom-videos` | PAUSED |
| **Ads (Sora-2 2-clip seamless)** | Web `speech` tab (paused) | `POST /api/ads/superbowl` | PAUSED / legacy |
| **Clip Management** | Web sidebar (paused) | `GET/POST/DELETE /api/clips` | Supporting — web only |
| **Stitch Clips** | Web sidebar (paused) | `POST /api/stitch` | Supporting — web only |

### Speech-to-Video Pipeline (Shipping — Core)

```
User (mobile): typed prompt OR recorded audio
  |
  v-- If audio: POST /api/transcribe (Whisper)
  v
  Mobile sends fixed model + duration (V1 has no picker):
    model = minimax/hailuo-2.3, duration = 10s
  |
  v-- POST /api/generate/speech-to-video {prompt, model, duration}
  Server: _check_credits_or_402 (10 credits required) → create_job → start_job
  |
  v-- In worker thread: video_service.generate_speech_to_video(text, model, duration)
    Hailuo via direct MiniMax client (MINIMAX_API_KEY required; returns error if not set)
  |
  v-- Mobile polls GET /api/jobs/{job_id} → video_url
  v-- Gallery screen renders clip
```

No multi-stage pipeline. No stitching. No GPT orchestration. One request = one clip.

### Timelapse-Phase-2 Pipeline (Paused)

The automated version of the freelancer's manual workflow. Not reachable from the shipping mobile app; kept for Timelapse-Phase-2 resumption:

```
User Input (room_type, style, features)
  |
  v-- Phase 1: Planning --
  GPT generate_scene_bible_only()
    -> scene_bible (300 char, immutable camera/room description)
    -> elements (5-7 functional categories: floor, walls, ceiling...)
    -> additions (elements not yet in room)
    -> stage_1_description (initial bare room state)
  |
  v-- Phase 2: Keyframe Generation (stages 1-7) --
  Stage 1: T2I (Nano Banana Pro) -> initial empty room image
  Stages 2-7 (iterative):
    GPT Vision sees prev image + cumulative room state -> plans next edit
    I2I (Nano Banana Pro Edit) generates edited image
    Room state accumulates: "floor = porcelain tiles; walls = warm paint"
    Early exit if all elements renovated before stage 7
  |
  v-- Phase 3: Transition Videos (6-7 transitions) --
  For each keyframe pair: I2V with first_frame + last_frame control
  Final pan shot from last keyframe (no last_frame constraint)
  |
  v-- Phase 4: Stitching --
  stitch_timelapse_clips(speed=1.5, hold_first_frame=2.0)
```

**Pause/resume:** `stop_after` ("plan", "stage_1"..."stage_7", "videos") + `resume_state` serialize full pipeline state at each checkpoint.

**Element tracking:** Renovated elements tracked with fuzzy name matching. Material dictionary builds cumulative room state for GPT context. Grouping hints force multi-element stages when budget is tight.

**Feature protection:** User design features explicitly protected in every GPT prompt — never removed, covered, or replaced.

### Key Components

**VideoService** (`src/speech_to_video/services/video_service.py`)
- Core orchestration for all pipelines
- `generate_speech_to_video(prompt, model, duration)`: **SHIPPING.** Single T2V clip. Routes Hailuo/MiniMax through direct MiniMax client; all others via AIMLAPI `_single_generation`.
- `generate_timelapse_v2()`: _paused._ 7-stage iterative pipeline with pause/resume + progress callbacks.
- `generate_custom_videos()`: _paused._ Image sequence -> GPT Vision transitions -> I2V.
- `generate_16s_video()`: _paused._ Seamless 2-clip generation with GPT prompt splitting.
- `generate_video()`: Routes to `_single_generation` (<=10s) or `_multi_generation` (>10s).
- `_single_generation()`: One AIMLAPI call + poll. Validates completion status AND direct media URL (.mp4/.webm).

**MiniMaxClient** (`src/speech_to_video/clients/minimax_client.py`)
- Direct MiniMax API for Hailuo T2V (bypasses AIMLAPI). Activated when `MINIMAX_API_KEY` is set.
- `generate_and_poll(prompt, model, duration, resolution)`: submit + poll until clip ready. This is the path the shipping product takes for Hailuo.

**KlingMotionClient** (`src/speech_to_video/clients/kling_motion_client.py`) — V2 Pipeline A + B
- Direct Kling API for Motion Control endpoint (bypasses AIMLAPI). Auth via HS256 JWT regenerated per request from `KLING_ACCESS_KEY` + `KLING_SECRET_KEY`.
- `generate_and_poll(image_url, video_url, character_orientation, mode, model_name, prompt, ...)`: submit + poll until clip ready. Returns `{success, video_url, task_id, duration}`.
- `character_orientation` selects the **character pose-orientation source**, NOT the scene source. Per S58 empirical (`Memory/feedback_provider_mode_names_neq_outcomes.md`), BOTH modes on their own produce Outcome 2 (motion-onto-character) — the input image's background wins in both cases. Kling Motion Control has no native Outcome-1 mode.
  - `"image"` → pose orientation taken from the reference image; driving video ≤10s. **Pipeline A** (viral dances) uses this on an NBP-cosmetically-edited character image.
  - `"video"` → pose orientation taken from the driving video; driving video ≤30s. **Pipeline B** uses this as its I2V step, AFTER NBP has already composited the character into the target scene. On its own this mode still produces Outcome 2 — it does NOT do scene composition; the Outcome-1 result of Pipeline B comes from the NBP pre-step, not from this mode.
- GET polls retry on 502/503/504 via urllib3; POST submit intentionally no-retry (avoids double-charge / duplicate moderation rejection).
- Output URL expires 30 days after generation — caller must rehost for longer retention.

**Nano Banana Pro (Pipeline B Edit)** — `gemini-3-pro-image-preview` via Google AI Studio direct (`genai.Client(api_key=NBP_API_Key)`). Locked S65; smoke `scripts/test_aistudio_nano_banana.py`. `vertex_ai_client.py` exists but is **not** the load-bearing path — to be migrated to a thin `gemini_client.py`.

**VertexAIClient** (`src/speech_to_video/clients/vertex_ai_client.py`) — original Vertex AI path for Nano Banana (T2I + Edit). Lazy `genai.Client(vertexai=True, project, location, credentials)`. Auth: `VERTEX_SERVICE_ACCOUNT_JSON` → `VERTEX_SERVICE_ACCOUNT_PATH`. Default model `VERTEX_NB_MODEL`. Retained until migration above lands.
- `generate_image_nano_banana(prompt, output_dir="/tmp")`: T2I. Returns `{success, local_path, model, mime_type}`.
- `edit_image_nano_banana(prompt, image_paths, output_dir="/tmp")`: Edit (selfie + scene → composite). Same return shape. Image inputs go inline as `Part.from_bytes`.

**OpenAIClient** (`src/speech_to_video/clients/openai_client.py`)
- `transcribe()`: Whisper with 3x retry (h11 errors, connection resets)
- `generate_scene_bible_only()`: Room analysis -> scene bible + elements + stage 1
- `generate_next_stage()`: GPT Vision sees prev image + room state -> plans next edit. 4 attempts with backoff, safe fallback on exhaustion
- `generate_transition_prompt()`: GPT Vision analyzes image pair -> 150 char transition prompt
- `split_prompt_for_two_clips()`: Find narrative break point for seamless 2-clip ads

**AIMLAPIClient** (`src/speech_to_video/clients/aimlapi_client.py`)
- **Dual HTTP sessions:** POST (2 manual attempts, no urllib3 retry) vs GET (urllib3 Retry: 3 retries, 0.8x backoff on 429/502/503/504)
- `generate_image()`: T2I (no image_urls) or I2I (with image_urls) via `/v1/images/generations`
- `generate_and_poll_i2v()`: Submit I2V + poll until complete. Auto-detects provider from model name (hailuo/seedance/kling) and adjusts endpoint + body
- `poll_until_complete()`: Max 600s default. Fallback to 3 alternate endpoints on 404
- `_extract_video_url()`: Recursive URL extraction, filters for .mp4/.webm only

**FastAPI Server** (`src/speech_to_video/api/server.py`)
- CORS: localhost:5173 + configurable `CORS_ORIGINS`
- **Auth: Firebase Bearer tokens** (mobile sends `Authorization: Bearer <firebaseIdToken>`). `verify_firebase_token` FastAPI dep in `api/firebase_auth.py` validates via `firebase-admin`, returns `{uid, is_anonymous, email, name, provider}`. No session middleware, no server-side OAuth.
- Credit gating: per-UID Firestore credit ledger via `utils/credit_store.py`. **All users gated identically** — anon users get 10 starter credits on first API call; signed-in users have only what they've purchased. `_check_credits_or_402` raises 402 on shortfall with `{required, balance}` payload. Per-gen cost: `CREDIT_COSTS[("hailuo", 10)] = 10`.
- Job endpoints: `POST /api/generate/speech-to-video` (shipping) and `POST /api/generate/timelapse` (paused) return `{job_id}`; poll via `GET /api/jobs/{job_id}`. Job stores `uid`/`credit_cost`; credits consumed atomically once on successful completion via `_maybe_consume_job_credits`.
- Clip CRUD: per-user namespace `{CLIPS_NAMESPACE}/{firebase_uid}`. Anonymous users get their own namespace.
- Public (no-auth) endpoints: `/api/health`, `/api/setup`, `/api/timelapse/options`, `/api/proxy-video`, `/api/debug/*`
- Video proxy: `GET /api/proxy-video?url=...` for external CDN URLs

**Job Manager** (`src/speech_to_video/utils/job_manager.py`)
- In-memory dict with threading.Lock, max 50 jobs, 1-hour TTL
- Daemon threads. Ephemeral — server restart loses all jobs
- Progress callback updates phase/step/message/partial_result

**Gen Telemetry** (`src/speech_to_video/utils/gen_telemetry.py`) — durable per-gen record in Firestore collection `gen_events` (the persistent counterpart to the ephemeral job manager; survives restarts, so failures don't depend on scraping the Replit console). The shipping motion-transfer path (`VideoService._dispatch_motion_transfer`) writes one doc per gen at every exit: `outcome`, `failure_stage`, `kling_task_id`, `last_task_status`, and per-stage timings (`prep_ms`, `kling_ms`, `total_ms`). Best-effort — never raises, can't fail a gen. Pipeline B (scene-insertion) is not yet instrumented.
- **Fire the report** (no Replit console needed): `python scripts/gen_telemetry_report.py [--failures-only] [--since-hours N] [--template <id>] [--limit N]`.
- **Interpret:** prints success rate, within-5-min / within-6-min SLA rates (target 99.99% — see `Memory/project_reliability_target_and_telemetry.md`), latency percentiles (p50/p90/p95/p99 of total + Kling), and a failure table. Failure `outcome`s: `timeout` (exceeded `max_wait` — read `last_task_status`: `submitted`=true hang vs `processing`=slow-but-alive), `kling_failed` (Kling rejected — moderation/internal), `submit_error`/`submit_no_task_id` (never got a Kling task), `empty_result` (Kling said succeed but no video URL), `nbp_error` (regen step failed). The `kling_task_id` lets you poll Kling directly (output URL lives 30 days).

**Clip Store** (`src/speech_to_video/utils/clip_store.py`)
- Filesystem: `clips/{namespace}/playlist.json`, `responses/{ts}.json`, `stitched/`
- Namespace sanitized: lowercase, non-alphanumeric -> `-`

**Video Utilities** (`src/speech_to_video/utils/video.py`)
- `stitch_videos()`: Basic with 0.5s crossfade (legacy)
- `stitch_videos_detailed()`: Same + detailed error dict
- `stitch_videos_seamless()`: NO visual crossfade, only 150ms audio fades (for ads)
- `stitch_timelapse_clips()`: Speed scaling + hold_first_frame + optional dissolve (for timelapses)
- `extract_first_frame()`: Extract video first frame to PNG. Accepts local path or http(s) URL. Optional thumbnail resize. Used by Pipeline A (driving-video preview tile) and Track 2 asset upload (auto-thumbnail).

**R2 Client** (`src/speech_to_video/utils/r2_client.py`) — V2 template asset hosting on Cloudflare R2 (S3-compatible). Public-read bucket served via custom domain `https://assets.speech-2-video.ai`, long-TTL cache (1y immutable), CF edge caching via the `Cache R2 assets` Cache Rule. Lazy `boto3` client, env-driven (raises `R2NotConfigured` if unset).
- `upload_file(local_path, key, content_type=None, cache_control=...)`: Upload file. Returns public URL.
- `public_url(key)`: Construct public URL under custom domain.
- `head_object(key)`, `delete_object(key)`: Metadata + delete.

**Timelapse Models** (`src/speech_to_video/models/timelapse.py`)
- `TimelapseRequest` dataclass: room_type, style, features, materials, lighting, camera_motion, progression, freeform_description
- `compose_timelapse_prompt()`: Builds prompt from request + narrative templates
- `get_all_options()`: 12 room types, 14 styles, 8 lighting, 6 camera, 3 progression, 20 features, 18 materials

### Mobile Frontend Architecture (Shipping)

**Expo Router (file-based)** under `mobile/app/`. State via **Zustand** stores (`mobile/store/`). Native `fetch` wrapped by `mobile/lib/api-client.ts`.

**Screens (`mobile/app/`):**
- `_layout.tsx` — root layout. Configures Firebase auth listener, RevenueCat (`configurePurchases()`), mounts the `Paywall` at the root.
- `(tabs)/index.tsx` — **the Speech-to-Video screen.** Model + duration selectors, text input, record button. Dispatches to `gallery-store.startGeneration()` which hits `/api/generate/speech-to-video`.
- `(tabs)/gallery.tsx` — generated clips list, video playback.
- `settings.tsx` — account + purchases UI.

**Stores (`mobile/store/`):**
- `auth-store.ts` — Firebase user, `canGenerate()`, `openPaywall()`, `loginRequired`/`paywallOpen` flags. Syncs RC user on auth change.
- `gallery-store.ts` — S2V job submission + polling + persisted gallery.
- `pipeline-store.ts` — **dormant** (wired for timelapse, no active UI).
- `clips-store.ts` — clip list for the (currently web-only) clips sidebar.

**Non-obvious component/lib behavior:**
- `Paywall.tsx` — full-screen modal (not a route), RC offering fetch, bundles Apple Sign In for anon users. Count from `PRO_PACK_COUNT` in `lib/constants.ts`, price from `pkg.product.priceString`.
- `VideoPlayer.tsx` — expo-av wrapper with URL preflight + 90s timeout safety net (silent fails are the failure mode, see `memory/project_video_player_test.md`).
- `lib/auth.ts` — Firebase anon + Apple Sign In, nonce pattern, anon→Apple linking preserves UID.
- `lib/purchases.ts` — `__DEV__` picks Test Store vs App Store SDK key.
- `lib/polling.ts` — adaptive intervals, tolerates 10 consecutive failures before pausing, AbortController per job.
- `lib/streaming.ts` — legacy SSE, being replaced by polling.

### Web Frontend Architecture (Paused)

**Single-page app with mode tabs** (no router). All state in `web/src/pages/App.tsx` (~1240 lines) via hooks. Native `fetch` (no axios). Components: `App.tsx`, `TimelapseForm.tsx`, `VideoStudio.tsx`, `MicVisualizer.tsx`, `ui/button.tsx`. **Not actively developed** — kept for reference.

### GPT Prompt Character Limits (Paused — Timelapse-Phase-2 only)

Not used by the shipping S2V pipeline (which passes the user prompt verbatim to the T2V model). Kept for reference when Timelapse work resumes.

| Field | Max Chars | Used In |
|-------|-----------|---------|
| Scene bible | 300 | Immutable camera/room description |
| Stage description | 200 | Initial stage visual state |
| Edit delta | 250 | What changes in a stage |
| Image prompt | 200 | Instruction for I2I edit model |
| Transition prompt | 150 | Motion/transformation for I2V |
| Material | 60 | Material for room state tracking |

### Configuration

All configuration via environment variables (`.env` file). Settings loaded via `src/speech_to_video/utils/config.py` — plain dataclass with `os.environ.get()` and `python-dotenv` (override=True).

**OpenAI:** `OPENAI_API_KEY`, `OPENAI_ORG_ID`, `OPENAI_PROJECT`, `OPENAI_CHAT_MODEL` (gpt-5.2), `OPENAI_TRANSCRIBE_MODEL` (whisper-1)

**AIMLAPI:** `AIMLAPI_API_KEY`, `AIMLAPI_BASE_URL`, `AIMLAPI_GENERATE_PATH`, `AIMLAPI_STATUS_PATH`, `AIMLAPI_STATUS_QUERY_PARAM`, retry/timeout/polling configs

**Models — Shipping (S2V T2V):** `HAILUO_23_T2V_MODEL` (default `minimax/hailuo-2.3` — the only model V1 ships). `MINIMAX_API_KEY` is **required** for the shipping path; without it `generate_speech_to_video` returns an error. (Legacy `KLING_T2V_MODEL` and `HAILUO_T2V_MODEL` env vars still exist in `config.py` for paused/historical work but are not read by the shipping S2V flow.)

**Models — Paused (Timelapse-Phase-2 + Ads):** `I2V_MODEL` (minimax/hailuo-02), `KLING_I2V_MODEL` (klingai/video-v3-pro-image-to-video), `SEEDANCE_I2V_MODEL`, `HAILUO_I2V_MODEL`, `AD_MODEL` (openai/sora-2-t2v), T2I: `google/nano-banana-pro`, I2I: `google/nano-banana-pro-edit`

**Auth:** `FIREBASE_SERVICE_ACCOUNT_PATH` (path to Firebase admin SDK JSON — supports `~` expansion). Anon free tier is now controlled by `_ANON_STARTER_CREDITS = 10` constant in `api/server.py` (not env-driven). Legacy `UNAUTH_GEN_LIMIT` env var and Google OAuth vars (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PUBLIC_BASE_URL`, `POST_LOGIN_REDIRECT`, `SESSION_SECRET`) are removed.

**Nano Banana Pro (AI Studio direct):** `NBP_API_Key` — Google AI Studio paid-tier key for `gemini-3-pro-image-preview` (Pipeline B Edit).

**Storage:** `CLIPS_NAMESPACE`, `CLIPS_DIR` (./clips/)

**R2 (V2 template asset hosting):** `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` (default `speech-to-video-templates`), `R2_PUBLIC_BASE_URL` (default `https://assets.speech-2-video.ai`). All four credentials required for `r2_client._s3()` to initialize; missing any raises `R2NotConfigured`. DNS hosted on Cloudflare (migrated from GoDaddy S61); Cache Rule `Cache R2 assets` ensures edge caching for the custom-domain hostname.

## API Endpoints

Enumerate via `grep '^@app\.' src/speech_to_video/api/server.py`. The Pipelines table above is the load-bearing map; signatures live in the code.

Auth contract: mobile sends `Authorization: Bearer <firebaseIdToken>`. No server-side login/callback/logout routes — mobile handles Apple Sign In + anonymous auth entirely via Firebase SDK; the server only verifies tokens.

## Development Standards

### Data Flow Verification Protocol

Before adding or modifying ANY rule/instruction in a GPT prompt that references specific data (user inputs, computed values, state), you MUST verify the data is actually available at that point in the pipeline.

**Mandatory checklist (every prompt change):**
1. **Identify referenced data**: What data does this rule need?
2. **Trace the origin**: Where does it come from? (UI input, API response, computed in code)
3. **Check the function signature**: Does the function receive this data as a parameter? READ the signature.
4. **Check the call site**: Does the caller actually pass it? READ the call site.
5. **Confirm end-to-end**: Data must flow from origin -> call site -> function -> prompt. If any link is missing, fix the pipeline BEFORE adding the prompt rule.

**If you violate this:**
1. Immediately acknowledge the mistake without waiting to be told
2. Audit EVERY other prompt rule in the same function for the same class of error
3. Fix all issues in a single pass — no iterative back-and-forth
4. Trace the full data flow for the fix and present it explicitly before implementing
5. You are NOT allowed to move on to any other task until the audit is complete and verified

### Implementation Quality Standards

**Self-verification (every change):**
1. **Bug check**: Trace all execution paths the change touches. Check for: stale references, missing parameters, broken control flow, uninitialized variables, off-by-one errors.
2. **Edge cases**: Empty lists, None optionals, early loop exits, no user features. Think through at least 3 scenarios.
3. **Side effects**: Does this change break existing behavior? Check callers, state snapshots, resume paths, frontend expectations.

**Robustness:**
- Get it right the first time. One well-thought-out change beats three iterative patches.
- Don't create infrastructure you'll tear down. Ask: is this the simplest solution?
- Every GPT instruction must give GPT the specific data it needs. Generic instructions without the actual data are useless.

**No hallucination — ZERO tolerance:**
- Never fabricate a root cause. If you don't have the data (JSON output, logs, prompts), ASK for it.
- Never assume inputs. If information is missing, ASK. Do not proceed without it.
- Pattern matching is not diagnosis. Every diagnosis must be grounded in evidence from the current run.
- Guessing a root cause and presenting it as fact is worse than saying "I don't know — can you share the output?"

**Think before acting:**
- Slow down. Check for missing inputs before jumping into analysis.
- If unsure about ANY aspect — intent, data, scope — ask. Do NOT fill gaps with assumptions.
- A wrong conclusion reached quickly is worse than a correct one reached after a clarifying question.

**Defensible responses only:**
- Every suggestion must withstand 3 follow-up questions. If not, don't present it.
- If you realize mid-thought you've drifted into a weak position, stop and change course immediately.
- Vague is indefensible. "Maximize visual contrast" without a measurable mechanism is not a suggestion.
- Speed is NOT the priority — quality is. A slow correct answer beats a fast wrong one.

**Internalize the vision:**
- You have the full conversation history. Use it to deeply understand the user's vision.
- You are not here to just write code. You are here to be a partner who shares the user's sense of what this app should become.
- The user is obsessed with their vision. If you don't internalize it, your responses will miss the mark.

**Intent understanding:**
- Read the full conversation, not just the last message. Understand the pattern.
- Anticipate follow-up issues. If a change fixes A but obviously causes B, flag it immediately.
- Don't over-engineer. Prefer general rules over hardcoding. Prefer dynamic injection over static examples.
- Each implementation should move the app closer to the goal. If the same class of issue keeps recurring, address the root cause.

## Recurring Patterns

- **Pause/resume via `stop_after` + `resume_state`**: Both timelapse and custom video pipelines serialize full state at each checkpoint.
- **Progress callbacks**: `on_progress(phase, step, total, message, partial_result)` flows VideoService -> Job Manager -> polling endpoint -> frontend.
- **Partial error recovery**: Multi-step pipelines return `{"success": false, ...accumulated_state}` for resume.
- **Provider auto-detection**: AIMLAPI client detects provider from model name and adjusts endpoint + body.
- **GPT Vision retry with fallback**: 4 attempts with exponential backoff, safe generic fallback on exhaustion.
- **Element fuzzy matching**: GPT-returned element names canonicalized to original list.
- **Four stitching modes**: basic, detailed, seamless (ads), timelapse (speed + frame hold).

## Common Pitfalls

- **AIMLAPI endpoint variation**: Providers expose different paths. Use env vars to configure.
- **Whisper upload errors**: h11 LocalProtocolError. Client retries 3x with backoff.
- **Stitching requires ffmpeg**: Via `imageio-ffmpeg` or system PATH.
- **Job manager is ephemeral**: In-memory, max 50, 1-hour TTL. Server restart loses all jobs. For a durable post-mortem of a gen (which stage failed, timeout vs reject, latency), use **Gen Telemetry** (Firestore `gen_events`) — see the component above and `scripts/gen_telemetry_report.py`.
- **Config is NOT pydantic-settings**: Plain dataclass with `os.environ.get()` and `python-dotenv` (override=True).
- **GPT model is gpt-5.2**: Set in .env, not the gpt-4 default in code.
- **Index-file conflicts: never blindly `git checkout --ours/--theirs`**: For files whose job is to enumerate other files (e.g., `Memory/MEMORY.md`, route registries, `__all__` lists, README TOCs, `package.json` deps), both sides of a conflict are usually *additive* — picking one silently drops the other side's entries and orphans whatever they pointed to. Always read the conflict markers and hand-merge. After resolving, scan the working tree for newly-added files the index would normally reference; orphans = index entries you just dropped. Full context: `Memory/feedback_index_files_need_handmerge.md`.

## Testing

No automated tests. Manual testing via the mobile app on simulator (`npx expo run:ios`) or TestFlight. Backend CLI, Gradio UI, and the paused web frontend exist but are not the primary test paths.

## Template creation (V2 motion-transfer dances)

Step-by-step procedure for creating a new V2 dance template (NBP edit → R2 → Kling chain → Firestore seed → publish) lives in `docs/V2_template_creation_runbook.md`. Always follow that runbook — past sessions converged to this exact shape and novel approaches reintroduce solved bugs. The per-template artifacts are: `scripts/test_<slug>_chain.py` (bespoke NBP prompt, for marketing preview only), `scripts/seed_<slug>_template.py` (Firestore fixture), and R2-public assets under `viral-dances/<slug>/`. As of S77 those assets are three files matching their roles: `raw_source.mp4` (source/revert), `driving_video.mp4` (high-bitrate Kling output = runtime driver), and `preview_stream.mp4` (~5 Mbps + faststart, what the app plays — raw Kling output stutters on mobile; built via `scripts/streaming_previews.py`). Names are URL-driven via Firestore fields — never delete a file by name (`driving_video.mp4` is load-bearing). See `Memory/reference_mobile_preview_bitrate_streaming.md`. Since S81 the seed also auto-generates a fourth asset — `thumbnail.jpg` (frame 0 of the preview) — and sets `assets.thumbnail_url`, so the home tile shows a first-frame poster instead of black while off-screen; the shared helper is `src/speech_to_video/utils/template_thumbnail.py` (`scripts/generate_template_thumbnails.py` is the catalog-wide backfill). Production runtime always uses the generic regen prompt + `nbp_framing_hint`, never the bespoke chain-script prompt — see `Memory/feedback_no_overfit_prompts.md`.

Runtime Kling `model_name` + `mode` are config-driven (AIV-101) via `VideoService._resolve_kling_settings` — flip without deploy via `scripts/set_kling_runtime.py` (global) or `scripts/set_template_kling_override.py` (per-template); details in `Memory/reference_kling_runtime_config_commands.md`.

## docs/ convention

`docs/api-notes/` is for static reference material (API request shapes, prompt templates we use). `docs/research/` is for spike outputs and competitor analysis — anything we generate or capture while evaluating providers, models, or competing products. When running a new provider spike, write a `motion-transfer-providers-{S##}.md`-style log into `research/` so the comparison data outlives the session.
