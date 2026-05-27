# Template Prep Folder Cleanup Runbook

How to safely clean the local template-creation scratch folder
(`~/Downloads/App Templates Prep/`) of source + intermediate files whose
shipping products are already live on R2. Companion to
`docs/V2_template_creation_runbook.md` (which *produces* these files) and the
recurring AIV-110 "stale-artifact cleanup" task.

First executed S81 (2026-05-27): `Done/` went 1.8 GB → 23 MB.

## The one safety rule

**Never decide a file is safe to delete from its filename.** A local file is
disposable only when the template's *shipping product* is verifiably live on R2
— i.e. its Firestore `assets.*_url` objects return HTTP 200. Filenames lie
(typos like `Na_Favelelinha…`, capital-vs-lowercase, abandoned-but-named-like-live
work such as `river_*`). This mirrors the rule in CLAUDE.md / NOW.md: *safe ID =
cross-ref Firestore URLs, NEVER filenames.*

The scratch folder holds **inputs**, not products: original downloads,
trimmed clips (`*_clip.mp4` → R2 `raw_source.mp4`), NBP edits (`*_edit_*.jpg`),
reference frames (`*_frame*.png`), Kling outputs (`*_chain_*.mp4` → R2
`driving_video.mp4`), and stream previews (`*_preview_stream.mp4` → R2
`preview_stream.mp4`). For a **live** template all of these are reproducible or
already on R2; for an **abandoned/unstarted** template they may be the only copy.

## Procedure

### 1. Inventory the target folder

```bash
DIR="$HOME/Downloads/App Templates Prep/Done"   # adjust subfolder
find "$DIR" -type f ! -name .DS_Store | sed 's/.*\.//' | tr 'A-Z' 'a-z' | sort | uniq -c   # extension mix
du -sh "$DIR"
find "$DIR" -maxdepth 1 -type f ! -name .DS_Store -exec stat -f '%z%t%N' {} \; \
  | awk -F'\t' '{sz=$1/1048576; n=$2; sub(".*/","",n); printf "%7.1f MB  %s\n", sz, n}' | sort -k4
```

### 2. Pull the live catalog from Firestore

```bash
cd /Users/saurabhsmacbookair/POCs/speech-to-video-generator
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('.env', override=True)
from src.speech_to_video.utils.template_registry import list_templates
for t in sorted(list_templates(published_only=False), key=lambda x:x['id']):
    a=t.get('assets') or {}
    print(t.get('published_status'), t['id'],
          (a.get('preview_video_url') or '').rsplit('/',1)[-1],
          (a.get('driving_video_url') or '').rsplit('/',1)[-1])
"
```

### 3. Prove the products are live on R2 (HEAD = 200)

Do NOT skip this — it's what makes "redundant" a fact, not an assumption.

```bash
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('.env', override=True)
from src.speech_to_video.utils.template_registry import list_templates
for t in list_templates(published_only=True):
    a=t.get('assets') or {}
    for k in ('preview_video_url','driving_video_url'):
        if a.get(k): print(a[k])
" > /tmp/r2_urls.txt
while read u; do
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' -I "$u")
  [ "$code" = 200 ] || echo "NOT-200 ($code): $u"
done < /tmp/r2_urls.txt
echo "checked $(wc -l < /tmp/r2_urls.txt) urls"
```

### 4. Bucket every file against the live catalog

Normalize each filename (lowercase, `-`/space → `_`) and match its prefix
against the live slug stems (longest-first), plus explicit aliases for files
named off-pattern (`dpwm`→`dont_play_with_me`, `beat_it_hubx`→`beat_it`,
`bad_open`→`bad`). Three buckets:

- **LIVE** — prefix matches a live slug whose R2 product passed step 3 → redundant, safe.
- **JUNK** — screenshots, error/failure captures, 0-byte stubs, orphan generic-named edits, stray test outputs → safe.
- **NOT LIVE** — no Firestore template (abandoned like `river_*`, unstarted, or
  personal/test like a `*_selfile.JPG`) → **hold for a human decision, never auto-delete.**

Print an `UNCLASSIFIED` bucket too and make sure it's empty before proceeding —
that's how the `Na_Favelelinha…` typo surfaced (it's the live na-favelinha source).

### 5. Stage to Trash (recoverable), not `rm`

Move the LIVE + JUNK buckets to a timestamped Trash subfolder so the step is
reversible until you empty it. **Hold the NOT-LIVE bucket out** and ask the
owner which (if any) to keep — abandoned sources can be wanted for a re-source
(e.g. River → AIV-109 non-Kling retry), and personal files (selfies) must never
be deleted silently.

```bash
DONE="$HOME/Downloads/App Templates Prep/Done"
TRASH="$HOME/.Trash/AppTemplatesPrep_Done_cleanup_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$TRASH"
find "$DONE" -maxdepth 1 -type f ! -name .DS_Store -print0 | while IFS= read -r -d '' f; do
  b=$(basename "$f"); bl=${b:l}                 # zsh lowercase — see pitfall below
  case "$bl" in
    river*|pinky*|madhvi*) continue ;;          # NOT-LIVE: keep for decision
  esac
  mv "$f" "$TRASH"/
done
```

### 6. Permanently delete, deletes before restores

After the owner decides, delete the staged pile and any NOT-LIVE files they
didn't keep. Order the irreversible deletes **before** moving any kept file back
into the folder, so a glob can't touch what you're keeping. Guard on the
keep-file's presence first.

```bash
KEEP="River_start_at_1_sec.mov"
[ -f "$TRASH/$KEEP" ] || { echo "ABORT: $KEEP missing"; exit 1; }
rm -f "$DONE"/river_* "$DONE/madhvi_dance.mp4"   # NOT-LIVE files the owner dropped
mv "$TRASH/$KEEP" "$DONE/"                        # restore the one keeper
rm -rf "$TRASH"                                   # purge the staged pile
ls -1 "$DONE" | grep -vi '^\.DS_Store$'           # confirm final state
```

## Pitfalls

- **This shell is zsh, not bash.** `shopt -s nocasematch` is bash-only; in zsh it
  errors and silently leaves `case`/glob matching **case-sensitive**, so
  capitalized filenames (`Pinky_Up.mp4`, `Madhvi_*`, `River_*`) slip past a
  lowercase-only filter. S81 swept those into Trash by mistake (caught before
  permanent deletion). Lowercase the variable yourself (`${b:l}`) — never reach
  for `shopt`. See `memory/feedback_zsh_not_bash.md`.
- **Dry-run first on anything destructive.** A filter bug is invisible until you
  diff intended-vs-actual; echo what *would* move/delete before executing.
- **Stage to Trash, confirm, then purge** — gives a recovery window for the
  inevitable filename surprise.
- **Don't touch `Working/` or `template_assets/`** unless explicitly asked — they
  hold in-progress and staging assets, not finished work.
