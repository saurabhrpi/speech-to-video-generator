---
name: firestore-partial-update-etag-stale
description: Partial Firestore .update({field: value}) does NOT bump updated_at, so the /api/templates ETag stays the same, mobile gets 304, and clients show stale data. Always bump updated_at alongside any partial update, or use upsert_template (which handles it).
metadata:
  type: reference
---

The `/api/templates` ETag is computed from sorted `id|updated_at` pairs (`src/speech_to_video/api/server.py:1293-1298`). Mobile sends its cached ETag in `If-None-Match`; the server returns `304 Not Modified` when ETags match, and mobile keeps its cached templates list.

**Trap:** `_doc_ref(template_id).update({"category": "..."})` (or any partial-field write) does NOT auto-update the `updated_at` field. The data changes in Firestore, but the ETag stays the same → mobile 304s → user sees stale templates forever (or until they manually clear app data).

**Verified S70:** flipped Beat It from `viral_dances` → `mj_dances` via `ref.update({"category": "mj_dances"})`. Curl without `If-None-Match` returned the new category correctly, but the iPhone + sim showed no change because their cached ETag matched the server's still-stale ETag.

**How to apply:**

- If you must do a partial update, include `updated_at`:
  ```python
  from google.cloud.firestore_v1 import SERVER_TIMESTAMP
  _doc_ref(tid).update({"category": "mj_dances", "updated_at": SERVER_TIMESTAMP})
  ```
- Or use `upsert_template(tid, full_data)` which manages `updated_at` itself — but it's a FULL replace, so include every field.
- The existing helper scripts (`scripts/set_template_status.py`, `set_template_audio.py`, etc.) all call through the registry helpers that bump `updated_at` correctly. If you find yourself writing a new partial-update script, mirror that pattern.
- After any partial update, sanity-check with `curl -sI https://speech-2-video.ai/api/templates | grep -i etag` — the value should change between before and after.
- Worth considering for V2.1: a Firestore trigger or write-through hook that always bumps `updated_at` on doc writes, so this trap goes away entirely.
