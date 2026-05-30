---
name: reference_legal_pages_served_by_fastapi
description: Live /privacy /terms /support are FastAPI HTML strings in legal.py, NOT Firebase Hosting — the "Google Frontend" header is Replit's GCP fronting
metadata:
  type: reference
---

The live legal pages at `https://speech-2-video.ai/{privacy,terms,support}` are served by our **own FastAPI backend** — `src/speech_to_video/api/legal.py` — as plain HTML strings (`_PRIVACY_BODY`, `_TERMS_BODY`, `_SUPPORT_BODY`) wrapped by `_shell()` + `_BASE_STYLE`. Routes: `@router.get("/privacy"|"/terms"|"/support")`.

**They are NOT Firebase Hosting.** S85 misdiagnosed this (NOW.md open Q#2) because `curl -sI` shows `server: Google Frontend` / `via: 1.1 google` — that header is just **Replit's GCP fronting** of the deployment, not Firebase. There is no `firebase.json`/`.firebaserc` anywhere and no separate hosting project for these pages. (Firebase IS used by the app — for auth + Firestore — just not for these pages.)

**To change the live legal pages:** edit the strings in `legal.py` directly (the file's docstring says so — "no separate hosting; git history is the changelog"), bump `EFFECTIVE_DATE`, commit, then **redeploy the backend to Replit** (Publish). The page is live only after that deploy — a repo edit alone does nothing. Constants at top: `SUPPORT_EMAIL`, `GOVERNING_LAW_JURISDICTION` (Tennessee), `GOVERNING_LAW_VENUE` (Davidson County, Tennessee).

Single source of truth — do NOT create parallel `docs/legal/*.md|html` copies (they drift). Mobile links these via `TERMS_URL`/`PRIVACY_URL` in `mobile/lib/constants.ts`. Content rewritten S86 (AIVO branding, 24h photo deletion, Google NBP + China cross-border + CCPA, 18+).
