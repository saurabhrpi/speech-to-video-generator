# V2 Template Creation Runbook

Step-by-step procedure for creating a new V2 motion-transfer dance template (Pipeline A — Kling Motion Control, Outcome 2). Captures the approach used across S65 (Bombale), S66 (Gangsta), S67 (Baby Dance), S70 (Beat It + Bad), S72 (Smooth Criminal + Thriller), and S73 (No Batidão).

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

Drop the source MP4 into `~/Downloads/App Templates Prep/`. The reference PNG is optional:

- **Source MP4** — the dance clip (typically >10s; will be trimmed). If the dance starts mid-clip, name the file `<Dance>_<N>sec_onwards.mp4` so the start offset is obvious.
- **Reference PNG (optional)** — a still image showing the kind of character/wardrobe/scene the template should evoke. Three sources, in order of preference:
  1. **First frame of the source MP4** (S73, No Batidão path). Extracted via `ffmpeg -ss 0 -t 1 -frames:v 1 first_frame.png`. Cleanest because the character + scene + UI overlays are exactly what the driving video shows; NBP can edit / regen against the very frames the dance plays over.
  2. **Competitor-app screenshot** (S65-S72 path, e.g. Bombale, Gangsta, Beat It). Has iOS UI overlays (status bar, close-X, dark UI panel). Will be cleaned up by NBP or Pillow.
  3. **Curated reference image** (rare). Only if neither (1) nor (2) is available.

### 2. Trim the source MP4 — 10s or 15s depending on Kling config

Driving video length is constrained by the Kling `character_orientation` you'll pick in step 7:
- `image` orientation → **≤10s** driving video
- `video` orientation → **≤30s** driving video (we cap at 15s in practice)

Default for new V2 templates: **15s + `character_orientation="video"`** (S73-locked, see [step 7](#7-run-the-kling-step) below). The longer driving clip captures more of the dance, and v2.6 outputs ~1:1 regardless of driving aspect (S58/S72 confirmed).

```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -ss <start> -i "<source>.mp4" -t 15 -c:v libx264 -preset fast -crf 18 \
  -c:a aac -movflags +faststart "<Slug>_clip.mp4"
```

`-ss <start>` placed **before** `-i` gives frame-accurate seek (re-encode, slower but reliable). `<start>` = the timestamp from the filename (e.g., `Bad_3sec_onwards.mp4` → `-ss 3`; `No_Batidao.mov` cropped from 1s → `-ss 1`). Use `-t 15` for the 15s default, or `-t 10` if you're staying on image-orientation.

### 3. Clean the reference PNG (only if it has UI overlays)

**Skip this step if your reference is the first frame of the source MP4** (S73 No Batidão path) — that frame's overlays get stripped by NBP in step 6.

**For competitor-app screenshots only:** iOS status bar (top ~120px) + dark UI panel (bottom). At 1284×2778, the dancer card occupies y=120 to y=1389. Crop conservatively:

```python
from PIL import Image
im = Image.open("<Slug>.PNG").convert("RGB")
im.crop((0, 120, 1284, 1370)).save("<Slug>_cropped.png")
```

The close-X overlay stays — NBP handles it in the next step (and falls back to Pillow paint per `Memory/feedback_nbp_wont_remove_ui_overlays.md` if NBP misses).

### 4. Write `scripts/test_<slug>_chain.py`

**Copy `scripts/test_no_batidao_chain.py` verbatim** (S73 reference shape — has explicit Kling config constants and the right defaults). Then change only:

```python
DEFAULT_REFERENCE = Path("/path/to/<reference>.png")

<SLUG>_EDIT_PROMPT = "..."  # see "NBP regen patterns" below

<SLUG>_DRIVING_VIDEO = (
    "https://assets.speech-2-video.ai/viral-dances/<slug>/driving_video.mp4"
)

# Kling config — leave these unless you have a specific reason to deviate.
KLING_CHARACTER_ORIENTATION = "video"   # 15s cap (vs image's 10s)
KLING_MODE = "pro"                      # catalog parity (1300-1500px); std is ~960px
KLING_MODEL_NAME = "kling-v2-6"         # half v3 cost; ~1:1 native aspect
```

And rename the references from `NO_BATIDAO_*` to `<SLUG>_*`.

**The bespoke per-template edit prompt is for the marketing preview generation ONLY.** Production runtime uses the GENERIC regen prompt + the template's `nbp_framing_hint`. See `Memory/feedback_no_overfit_prompts.md` — prompt cores stay generic in production; specifics live in Firestore.

#### NBP regen patterns

Two patterns, pick based on what's in your reference image:

##### Pattern A — Preserve-identity wardrobe-swap (S65-S72 default)

Use when the reference person should LOOK like the person in the output (face/hair/body unchanged; just wardrobe + scene change). Past templates: Bombale, Gangsta, Baby Dance, Beat It, Bad, Smooth Criminal, Thriller.

```python
<SLUG>_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Remove the dark circular X close-button in the top-left corner. "
    "Paint over it with what would naturally be behind it.\n"
    "- Change the outfit to <new outfit description>.\n"
    "- Change the background to <new scene description>.\n"
    "- Preserve the person's face, hair, body shape, skin tone, and identity exactly.\n"
    "- Output a clean photographic frame with no UI elements."
)
```

##### Pattern B — Holistic-regen with DIFFERENT subject (S73 hybrid-permissive default)

Use when the reference person should NOT appear in the output (e.g., the source frame is an identifiable real person whose likeness shouldn't end up in our marketing asset, or you want a generic stand-in instead of the specific source dancer).

**Approach: hybrid-permissive.** Constrain what NOT to do, give NBP a small menu of options, specify *register* not *specifics*. See `Memory/feedback_nbp_hybrid_default.md`. This is S73-locked — don't re-debate the explicit-vs-implicit axis per template.

```python
<SLUG>_EDIT_PROMPT = (
    "Edit this image:\n"
    "- Replace the subject with a DIFFERENT young [woman|man|child] — "
    "similar age (<age range>), <build>. Different facial features and "
    "identity from the input. Different [hair color OR style] (e.g. <opt1>, "
    "<opt2>, or <opt3> — pick one). <mood> expression. Same general "
    "<pose register> standing dance pose.\n"
    "- Wardrobe: register that is NOT the input's <input wardrobe>. "
    "E.g. <opt1>, <opt2>, or <opt3> — pick one. <complementary bottom + "
    "footwear menu>.\n"
    "- Scene: similar register to the input but distinct composition. "
    "E.g. <opt1>, <opt2>, or <opt3>. Soft natural daylight, <vibe>.\n"
    "- Remove ALL UI overlays from the input: <enumerate each one — record "
    "indicators, close buttons, status bar icons, captions>. Paint over each "
    "with what would naturally be behind it.\n"
    "- Output a clean photographic frame at square (1:1) aspect — no UI, "
    "no buttons, no text overlays. Full body head-to-feet with comfortable "
    "headroom and floor visible under the feet. The face MUST be clearly "
    "visible (do not crop the head or chin)."
)
```

**Key shape rules (do not deviate):**
- **Constrain NOT-to-do**, then give a menu. "Different from the input's beige" → "(e.g. olive, sage, sand — pick one)."
- **Specify register, not specifics.** "cozy domestic interior" beats "wooden block toys on a plush rug under a sheer-curtained window."
- **Composition lock (S73 critical).** ALWAYS include: *"Subject must occupy the SAME proportion of the frame as the person in the input image — same head position, same body size relative to the frame edges. Do NOT zoom in, do NOT zoom out, do NOT move the subject closer to or further from the camera. Preserve the input's camera-to-subject distance and framing exactly."* Required to prevent Kling from hallucinating duplicate subjects when the driving video has camera-approach motion (S73 Beat It Hubx failure mode). See `Memory/feedback_nbp_hybrid_default.md`.
- **Enumerate UI overlays explicitly** — vague "remove the UI" misses items per `Memory/feedback_nbp_wont_remove_ui_overlays.md`.
- **Generic graphic spec** for any printed graphics — "no readable text, no logos, just a small abstract graphic" — avoids NBP fabricating illegible glyphs.
- **Force face visibility** — explicit "do not crop head or chin" guards against NBP preserving a chin-cropped source frame's composition (S73 Smooth Criminal Hubx — `t=0` frame was chin-cropped; switched to `t=1s` AND added the explicit constraint).

**Empirical record (S73):**
- ✅ Baby Dance Hubx — first attempt clean (mint joggers + chestnut curls + cozy home).
- ✅ Smooth Criminal Hubx — first attempt clean (burgundy ribbed knit + loft brick wall + face visible).
- ✅ No Batidão — first attempt clean (Pattern B was first piloted here; earlier draft of this section used a fully-explicit shape that also worked but was over-engineered).
- ⚠️ Beat It Hubx v1 — too close to input (fully-explicit "fair-to-medium skin, beige linen, park canopy" locked NBP into the source register). v2 with the hybrid-permissive shape produced a visibly distinct result. Lesson: when the source's wardrobe + scene are already in a specific niche register, fully-explicit specs that *match* that niche register cause NBP to anchor too close to the input. Use NOT-this-register + menu to push NBP off the anchor.

**If a first-pass output is too close to the input** — chain a second NBP pass: feed the v1 NBP edit as the reference, and write a prompt with explicit "MUST be visually distinct from this reference" + menu of alternatives. See `scripts/test_beat_it_hubx_chain.py` history and the inline-Python v2 pattern from S73.

#### Aspect-ratio control (when source is portrait)

If the reference PNG is portrait (taller than wide), NBP will produce a portrait output and Kling will inherit that portrait aspect — clipping lateral arm gestures (S72 Thriller debug). To force ~1:1 Kling output from a portrait source, use the **wide-arms T-pose framing** in the NBP prompt:

```
- POSE: standing upright facing the camera, with BOTH ARMS extended WIDE to
  the sides (full wingspan, T-pose), palms facing forward. Feet hip-width apart.
- COMPOSITION: square or near-square aspect ratio (1:1). The frame MUST
  accommodate the full arm wingspan with comfortable room on both LEFT and
  RIGHT sides — do NOT clip the fingertips at the side edges.
```

See `Memory/reference_kling_mc_aspect_inherits_nbp.md` (S73 confirmed). Skip this for sources that are already ~1:1 (e.g. first frame extracted from a square driving video).

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

`--no-update-registry` because the Firestore doc doesn't exist yet — we seed it in step 10. The script prints the resulting public URL; verify it matches the constant in step 4.

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

Inspect the resulting `~/Downloads/<slug>_chain_<hash>.mp4`. Expected output (S73 defaults — v2.6 + pro + video + 15s):
- Resolution: ~1440×1440 (1:1), or whatever aspect the NBP edit had
- Bitrate: 14-22 Mbps native from Kling
- Duration: matches the driving video (up to 15s)
- Cost: ~$1.50 Kling-side per gen (vs ~$2 if you accidentally ran v3)
- Elapsed: 3-6 min

**Preview vs. runtime cost split** — see `Memory/project_kling_mode_split.md`. Chain scripts run with `pro` mode for catalog-quality preview; runtime user gens in `video_service.py` run with `std` mode (~$0.50 Kling-side) for unit-cost. Both pinned to `kling-v2-6`. **Do not flip the runtime call sites in `video_service.py:969` and `:1126` to pro** — that doubles per-gen cost. Future consideration: bump preview-only to `kling-v3` for facial-consistency; spike A/B before flipping.

**Audio: ON for dance templates.** Pass `--keep-audio` so the preview video preserves the driving video's soundtrack. The home-screen tile auto-mutes via `isMuted` on the `<Video>` component (`mobile/app/index.tsx:TemplateTile` + `HeroCard`), so multiple tiles never blare music at once. Audio is heard only on the detail screen / generated gen playback. The `audio_enabled` Firestore flag must also be set True in the seed (step 10). V3 will introduce an audio-swap step; until then, the driving video's audio rides through.

### 8. (Optional) Trim the preview before uploading

If the Kling output has dead frames at the start/end (e.g., explicit content in the last seconds, dancer not in frame at t=0), temporal-trim with ffmpeg before upload. **Use `-crf 15`** (not 18) to keep bitrate close to Kling's native ~20 Mbps — see `Memory/feedback_template_preview_crf.md`. If no trim is needed (Kling output is clean start-to-end at the right length), skip this step and upload Kling's raw output as-is to preserve native bitrate.

```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -y -ss <start> -t <duration> -i ~/Downloads/<slug>_chain_<hash>.mp4 \
  -c:v libx264 -preset medium -crf 15 \
  -c:a aac -b:a 128k \
  ~/Downloads/template_assets/viral-dances/<slug>/preview_video.mp4
```

### 8b. (Optional) Audio-sync correction — `-itsoffset` for the Kling audio lead

Kling Motion Control introduces a **~0.5s audio lead** on its output (you hear the lyrics *before* the lips move). This is **intrinsic to Kling's output**, NOT the driver — confirmed S76: re-encoding the driver to clean CFR + flattening edit lists + removing VFR did NOT fix it, and neither did flipping v2.6→v3 (v3 only delivered faster). The only working fix is an output-side audio delay. See `Memory/feedback_kling_audio_lead_and_preview_propagation.md`.

**Skip this step if the preview's audio already lands on the lips** — not every clip shows a noticeable lead.

If audio leads, delay it (stream-copy, no quality loss). Exact magnitude can only be judged by ear — bracket and pick:

```bash
FF=$(.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
IN=~/Downloads/<slug>_chain_<hash>.mp4
for D in 0.40 0.50 0.60; do
  "$FF" -y -i "$IN" -itsoffset $D -i "$IN" \
    -map 0:v:0 -map 1:a:0 -c copy -shortest -movflags +faststart \
    ~/Downloads/<slug>_shift_${D/./p}.mp4
done
# Watch all three; pick the one where lyrics land on the mouth. 0.5s was the answer for DPWM (S76).
```

The delay leaves ~Ds of silent video at the head. To avoid a "dead" open, trim that head — re-encode at crf 15 for catalog parity (the one place you re-encode the preview). **Tradeoff:** trimming the head drops the first ~Ds of dance footage; the music stays intact from its start. You can't keep all footage AND avoid a silent open AND have frame-one sync — pick two.

```bash
"$FF" -y -ss 0.5 -i ~/Downloads/<slug>_shift_0p50.mp4 \
  -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart \
  ~/Downloads/template_assets/viral-dances/<slug>/preview_video.mp4
```

If you run this step, the shifted-and-trimmed file IS your `preview_video.mp4` — skip the step-8 trim (already re-encoded) and go straight to step 9 upload.

**Runtime caveat:** under preview-as-driver, runtime user gens likely exhibit the same lead (Kling re-applies it on every output; a corrected driver doesn't prevent it). Whether the preview fix propagates is **unverified** — verify with one real gen, and if confirmed apply the per-template `audio_offset_sec` runtime fix (Task 4 / AIV).

### 9. Upload the preview video to R2 public

```bash
# If you skipped step 8, stage the raw Kling output:
cp ~/Downloads/<slug>_chain_<hash>.mp4 \
   ~/Downloads/template_assets/viral-dances/<slug>/preview_video.mp4

.venv/bin/python scripts/upload_template_assets.py \
  ~/Downloads/template_assets \
  --template viral-dances-<slug> \
  --no-update-registry
```

### 10. Write `scripts/seed_<slug>_template.py`

**Copy `scripts/seed_baby_dance_template.py` verbatim**, then change only:

- `TEMPLATE_ID = "viral-dances-<slug>"`
- `<SLUG>_FIXTURE["title"]` — the user-facing title (e.g., `"Beat It"`)
- `<SLUG>_FIXTURE["description"]` — the user-facing one-liner with emoji
- `<SLUG>_FIXTURE["assets"]["driving_video_url"]` — point to the URL from step 5
- `<SLUG>_FIXTURE["assets"]["preview_video_url"]` — point to the URL from step 9
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

### 11. Run the seed

```bash
.venv/bin/python scripts/seed_<slug>_template.py
```

Writes the doc with `STATUS_DRAFT` — the template won't appear in the mobile gallery yet (gallery filters to `published`).

**If the current global policy is preview-as-driver** (S74 A/B — check via `scripts/set_preview_template_driving_video.py --all --show`), align the new template to the same policy before sim-testing:

```bash
.venv/bin/python scripts/set_preview_template_driving_video.py \
    --template-id viral-dances-<slug> --use-preview
```

This is idempotent and surgical — only this template's `driving_video_url` is flipped, original is preserved in `assets.original_driving_video_url` for revert. Skip this sub-step if global policy is the raw-driver default.

### 12. Sim test

```bash
cd mobile && npx expo run:ios
```

Open the **published** templates list manually in dev (e.g., add a debug toggle, or flip status temporarily) and confirm the tile preview video plays. End-to-end test: tap a published template → upload a real selfie → run gen → confirm the runtime production path produces a coherent output. Production NBP regen uses the generic prompt + `nbp_framing_hint`, NOT the bespoke edit prompt from step 4.

### 13. Flip to published

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
- **Credit cost = 25.** Per S68. Older seed scripts (bombale/gangsta/baby-dance) still hold 23 — drift to fix in V2.0.1.
- **Preview vs. runtime Kling config split.** Chain scripts (preview build): `pro` mode + `kling-v2-6` hardcoded in each `test_<slug>_chain.py`. Runtime (user gens): resolved per-request via `VideoService._resolve_kling_settings` (AIV-101) — per-template override → global Firestore `config/runtime` → hardcoded fallback (currently `kling-v2-6 + std`). Flip the global with `scripts/set_kling_runtime.py --preset v2-6-std|v2-6-pro|v3-std|v3-pro`; pin one template with `scripts/set_template_kling_override.py`. Propagation ≤30s, no redeploy. See `Memory/reference_kling_runtime_config_commands.md` for the full command list. Cost: `v3-pro` ~$2/gen vs `v2-6-std` ~$0.50/gen — flipping global is a per-user-gen economic decision, not just a quality knob.
- **Driving-video source policy.** Two states exist today: (a) raw driver (the canonical source MP4 from R2) — historical default; (b) preview-as-driver (S74 A/B) — `driving_video_url` points at the same R2 object as `preview_video_url`. Toggle catalog-wide with `scripts/set_preview_template_driving_video.py --all --use-preview` (flip) or `--all --revert` (back to raw). New templates require a one-extra-line sub-step at runbook step 11 to stay aligned with the active policy — see that step. The script ALWAYS preserves the raw URL in `assets.original_driving_video_url` on first overwrite, so revert is safe across any number of flips. Idempotent — re-running on already-flipped templates is a no-op.
- **Audio ON for dance templates.** Set `audio_enabled: True` in the seed fixture; pass `--keep-audio` to spike chain scripts. The home-screen tile mutes client-side via `isMuted`. Audio plays only on the detail screen / gen playback. V3 will introduce an audio-swap step. See `Memory/project_kling_audio_test_policy.md` (the "default off" note in that memory refers to the legacy S66 stance — superseded for dance templates).
- **Driving video filename:** new templates use `driving_video.mp4`; older templates (bombale/gangsta/baby-dance) used `driving_video_10s.mp4`. Both work; pick `driving_video.mp4` for new ones.
- **Re-uploads need a CF cache purge.** The templates R2 bucket sets `Cache-Control: public, max-age=31536000, immutable`, so overwriting the SAME key leaves CF edges serving the old version for up to a year. When you replace an asset mid-build (delogo, upscale, re-encode), the workflow is: (1) overwrite the R2 object at the canonical key, (2) run `.venv/bin/python scripts/purge_cf_cache.py <url>` to invalidate the CDN edge. Confirm with `curl -sI <url> | grep content-length` matches the new file size. Keep the canonical filename (`driving_video.mp4`) — do NOT version-suffix files to dodge the purge step; that creates URL noise that compounds across templates.
- **Trim-step CRF: 15, not 18.** When step 8 is needed (temporal trim of Kling output before R2 upload), use `-crf 15` or lower. Visually identical to crf-18 on today's iPhones, but leaves bitrate headroom closer to Kling's native ~20 Mbps and matches the catalog-template parity bar. See `Memory/feedback_template_preview_crf.md`.
- **Aspect inherits NBP.** Kling output aspect is inherited from the NBP edit's aspect — see `Memory/reference_kling_mc_aspect_inherits_nbp.md`. If the source is portrait, either crop to ~1:1 before NBP, or use the wide-arms T-pose framing in the NBP prompt (step 4).
- **Pattern smell.** With 9+ templates, the per-template sister-script pattern (`test_<slug>_chain.py` × N, `seed_<slug>_template.py` × N) is overdue for generalization. Don't refactor mid-build — finish the templates, then generalize.
- **NBP close-X removal is inconsistent.** `Memory/feedback_nbp_wont_remove_ui_overlays.md` — if it fails once, fall back to Pillow paint rather than re-prompting NBP.
