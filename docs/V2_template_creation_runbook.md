# V2 Template Creation Runbook

Step-by-step procedure for creating a new V2 motion-transfer dance template (Pipeline A — Kling Motion Control, Outcome 2). Captures the approach used across S65 (Bombale), S66 (Gangsta), S67 (Baby Dance), and S70 (Beat It + Smooth Criminal + Pinky Up + Bad + Rasputin).

If you find yourself deviating from this runbook, **stop and re-read it**. Past sessions have repeatedly converged to this exact shape; novel approaches almost always reintroduce bugs the existing pattern already solved.

## Per-template artifacts (final state)

Each shipped template results in:

| Artifact | Location | Type |
|---|---|---|
| Driving video (cropped to 10s) | `https://assets.speech-2-video.ai/viral-dances/<slug>/driving_video.mp4` | R2 public |
| Preview video (NBP→Kling chain output) | `https://assets.speech-2-video.ai/viral-dances/<slug>/preview_video.mp4` | R2 public |
| Thumbnail (optional fallback poster) | `https://assets.speech-2-video.ai/viral-dances/<slug>/thumbnail.jpg` | R2 public |
| Firestore template doc | `templates/viral-dances-<slug>` | Firestore (Pipeline A) |
| Chain spike script | `scripts/test_<slug>_chain.py` | repo |
| Seed script | `scripts/seed_<slug>_template.py` | repo |

Note: the template tile in the home grid renders `assets.preview_video_url ?? assets.driving_video_url` as a looping `<Video>` (see `mobile/app/index.tsx:TemplateTile`). The thumbnail field is a fallback poster, not the primary tile media — past templates have left it null and the tile still works fine.

## Step-by-step (per template)

### 1. Source assets

Drop the source PNG + source MP4 into `~/Downloads/App Templates Prep/`:

- **Reference PNG** — a still image showing the kind of character/wardrobe/scene the dance template should evoke. Often a competitor-app screenshot with iOS UI overlays (status bar, close-X, dark UI panel). Will be cleaned up + edited by NBP.
- **Source MP4** — the dance clip (typically >10s; will be cropped). If the dance starts mid-clip, name the file `<Dance>_<N>sec_onwards.mp4`.

### 2. Crop the source MP4 to 10 seconds

```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -ss <start> -i "<source>.mp4" -t 10 -c:v libx264 -preset fast -crf 18 \
  -c:a aac -movflags +faststart "<Slug>_clip.mp4"
```

`-ss <start>` placed **before** `-i` gives frame-accurate seek (re-encode, slower but reliable). `<start>` = the timestamp from the filename (e.g., `Bad_3sec_onwards.mp4` → `-ss 3`). For sources without a timestamp, use `-ss 0`.

### 3. Pillow-crop the reference PNG (if it has UI overlays)

Competitor-app screenshots have iOS status bar (top ~120px) + dark UI panel (bottom). At 1284×2778, the dancer card occupies y=120 to y=1389. Crop conservatively:

```python
from PIL import Image
im = Image.open("<Slug>.PNG").convert("RGB")
im.crop((0, 120, 1284, 1370)).save("<Slug>_cropped.png")
```

The close-X overlay stays — NBP handles it in the next step (and falls back to Pillow paint per `Memory/feedback_nbp_wont_remove_ui_overlays.md` if NBP misses).

### 4. Write `scripts/test_<slug>_chain.py`

**Copy `scripts/test_baby_dance_chain.py` verbatim**, then change only these constants:

```python
DEFAULT_REFERENCE = Path("/path/to/<Slug>_cropped.png")

<SLUG>_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Remove the dark circular X close-button in the top-left corner. Paint over it...\n"
    "- Change the outfit to <new outfit>.\n"
    "- Change the background to <new scene>.\n"
    "- Preserve the person's face, hair, body shape, skin tone, and identity exactly.\n"
    "- Output a clean photographic frame with no UI elements..."
)

<SLUG>_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/<slug>/driving_video.mp4"
)
```

And rename the references from `BABY_DANCE_*` to `<SLUG>_*` (or the dance name in caps).

The bespoke per-template edit prompt is **for the marketing preview generation only**. Production runtime uses the GENERIC regen prompt (`_GENERIC_NBP_REGEN_PROMPT` in `video_service.py`) + the template's `nbp_framing_hint`. See `Memory/feedback_no_overfit_prompts.md` — prompt cores stay generic in production; specifics live in Firestore.

### 5. Upload the driving video to R2 public

Stage the file into the canonical nested layout, then run the bulk uploader:

```bash
mkdir -p ~/Downloads/template_assets/viral-dances/<slug>
cp "~/Downloads/App Templates Prep/<Slug>_clip.mp4" \
   ~/Downloads/template_assets/viral-dances/<slug>/driving_video.mp4

.venv/bin/python scripts/upload_template_assets.py \
  ~/Downloads/template_assets \
  --template viral-dances-<slug> \
  --no-update-registry
```

`--no-update-registry` because the Firestore doc doesn't exist yet — we seed it in step 8. The script prints the resulting public URL; verify it matches the constant in step 4.

### 6. Run the NBP step

```bash
.venv/bin/python scripts/test_<slug>_chain.py --no-kling
```

Inspect the saved edit (`~/Downloads/<slug>_edit_*.jpg` or `.png`). If the close-X overlay survived (per `Memory/feedback_nbp_wont_remove_ui_overlays.md`) or the outfit/background doesn't match the creative direction, **iterate the edit prompt** — don't proceed.

### 7. Run the Kling step

Once the edit is approved:

```bash
.venv/bin/python scripts/test_<slug>_chain.py \
  --edited-image ~/Downloads/<slug>_edit_<hash>.jpg \
  --keep-audio
```

Costs ~25 credits (Kling Motion Control). Inspect the resulting `~/Downloads/<slug>_chain_<hash>.mp4`.

**Audio: ON for dance templates.** Pass `--keep-audio` so the preview video preserves the driving video's soundtrack. The home-screen tile auto-mutes via `isMuted` on the `<Video>` component (`mobile/app/index.tsx:TemplateTile` + `HeroCard`), so multiple tiles never blare music at once. Audio is heard only on the detail screen / generated gen playback. The `audio_enabled` Firestore flag must also be set True in the seed (step 9). V3 will introduce an audio-swap step; until then, the driving video's audio rides through.

### 8. Upload the preview video to R2 public

```bash
cp ~/Downloads/<slug>_chain_<hash>.mp4 \
   ~/Downloads/template_assets/viral-dances/<slug>/preview_video.mp4

.venv/bin/python scripts/upload_template_assets.py \
  ~/Downloads/template_assets \
  --template viral-dances-<slug> \
  --no-update-registry
```

### 9. Write `scripts/seed_<slug>_template.py`

**Copy `scripts/seed_baby_dance_template.py` verbatim**, then change only:

- `TEMPLATE_ID = "viral-dances-<slug>"`
- `<SLUG>_FIXTURE["title"]` — the user-facing title (e.g., `"Beat It"`)
- `<SLUG>_FIXTURE["description"]` — the user-facing one-liner with emoji
- `<SLUG>_FIXTURE["assets"]["driving_video_url"]` — point to the URL from step 5
- `<SLUG>_FIXTURE["assets"]["preview_video_url"]` — point to the URL from step 8
- `<SLUG>_FIXTURE["credit_cost"]` — **25** (per S68, NOT 23 as the older fixtures still hold)

Keep these unchanged:
- `pipeline_class = PIPELINE_MOTION_TRANSFER`
- `outcome = OUTCOME_ONTO_CHARACTER`
- `category = "viral_dances"` for generic viral dances; `category = "mj_dances"` for Michael Jackson dances (Beat It, Smooth Criminal, Bad). New category labels need a corresponding entry in `CATEGORY_LABEL_OVERRIDES` in `mobile/app/index.tsx` so abbreviations render correctly (e.g. `mj_dances → MJ Dances`, not "Mj Dances"). Without the override, `prettyCategory()` mechanically title-cases each word and breaks abbreviations.
- `published_status = STATUS_DRAFT`
- `model = "kling-2.6-motion-control-image"`
- `prompt_template = GENERIC_KLING_PROMPT` (the coherence prompt — identical across all templates)
- `use_nbp_regen = True`
- `nbp_framing_hint = "Composition: full body standing pose, head to feet."` (full-body framing — same hint across all dance templates to date)
- `is_hero = False`, `hero_order = None`
- `audio_enabled = True` (dance templates ship with audio ON; home-tile is muted client-side via `isMuted`)

### 10. Run the seed

```bash
.venv/bin/python scripts/seed_<slug>_template.py
```

Writes the doc with `STATUS_DRAFT` — the template won't appear in the mobile gallery yet (gallery filters to `published`).

### 11. Sim test

```bash
cd mobile && npx expo run:ios
```

Open the **published** templates list manually in dev (e.g., add a debug toggle, or flip status temporarily) and confirm the tile preview video plays. End-to-end test: tap a published template → upload a real selfie → run gen → confirm the runtime production path produces a coherent output. Production NBP regen uses the generic prompt + `nbp_framing_hint`, NOT the bespoke edit prompt from step 4.

### 12. Flip to published

```bash
.venv/bin/python scripts/set_template_status.py viral-dances-<slug> published \
  --reason "S<NN> sim verified"
```

Optionally enable as hero:

```bash
.venv/bin/python scripts/set_template_hero.py \
  --template-id viral-dances-<slug> --enable --order <N>
```

## Notes & gotchas

- **Bespoke vs generic NBP prompt.** The `test_<slug>_chain.py` script uses a bespoke per-template edit prompt to produce the marketing preview asset. Production runtime uses the generic regen prompt — never the bespoke one. Do not move the bespoke prompt into Firestore.
- **Credit cost = 25.** Per S68. Older seed scripts (bombale/gangsta/baby-dance) still hold 23 — that's drift to fix in V2.0.1 (NOW.md S69 item #9).
- **Audio ON for dance templates.** Set `audio_enabled: True` in the seed fixture; pass `--keep-audio` to spike chain scripts. The home-screen tile mutes client-side via `isMuted`. Audio plays only on the detail screen / gen playback. V3 will introduce an audio-swap step. See `Memory/project_kling_audio_test_policy.md` (the "default off" note in that memory refers to the legacy S66 stance — superseded for dance templates).
- **Driving video filename:** new templates use `driving_video.mp4`; older templates (bombale/gangsta/baby-dance) used `driving_video_10s.mp4`. Both work; pick `driving_video.mp4` for new ones.
- **Re-uploads need a CF cache purge.** The templates R2 bucket sets `Cache-Control: public, max-age=31536000, immutable`, so overwriting the SAME key leaves CF edges serving the old version for up to a year. When you replace an asset mid-build (delogo, upscale, re-encode), the workflow is: (1) overwrite the R2 object at the canonical key, (2) run `.venv/bin/python scripts/purge_cf_cache.py <url>` to invalidate the CDN edge. Confirm with `curl -sI <url> | grep content-length` matches the new file size. Keep the canonical filename (`driving_video.mp4`) — do NOT version-suffix files to dodge the purge step; that creates URL noise that compounds across templates.
- **Pattern smell.** With 8+ templates, the per-template sister-script pattern (`test_<slug>_chain.py` × N, `seed_<slug>_template.py` × N) is overdue for generalization (NOW.md S69 item #7). Don't refactor mid-build — finish the templates, then generalize.
- **NBP close-X removal is inconsistent.** `Memory/feedback_nbp_wont_remove_ui_overlays.md` — if it fails once, fall back to Pillow paint rather than re-prompting NBP.
