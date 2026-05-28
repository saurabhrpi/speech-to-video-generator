---
name: feedback_persist_accepted_nbp_edit
description: Never let the final/accepted NBP character edit get deleted — it's the only clean source for reusing a template's character
metadata:
  type: feedback
---

The final **accepted NBP-edited character image** for a template must NOT be allowed to disappear. Today the chain scripts (`test_<slug>_chain.py:run_kling`) upload the approved edit only to the PRIVATE selfies bucket under `spike-outputs/<random-hash>.png` — an ephemeral, unnamed key with no retention. It is never persisted as a durable named template asset. So once the local `~/Downloads/<slug>_edit_*.png` is cleaned up, the clean character is gone.

**Why:** S82 — to build Soda Pop Baby Dance the user wanted to reuse the baby from the already-live Mapopo template ("just take the baby from Mapopo"). The accepted Mapopo NBP edit no longer existed anywhere recoverable (not on R2 as a named asset, not on disk), so we had to **re-extract the character from the compressed/lossy `preview_video.mp4`** — a manual frame-grab at reduced quality instead of the pristine edit. Wasteful and lossy; reuse should have been one URL.

**How to apply:**
- Keep the final accepted NBP edit — the SPECIFIC roll that was fed to Kling, not the whole glob. Pattern B often takes 2-3 rolls (`<slug>_edit_<hashA>.png`, `<hashB>.png`, …); the rejected intermediate rolls ARE disposable and may be swept. Only the one approved/used edit must survive — identify it by the exact `--edited-image` path that the chain's Kling step consumed, not by the `<slug>_edit_*.png` wildcard. Don't sweep that file in cleanup runbooks until the template ships, and ideally keep it after.
- Going forward, persist the accepted edit as a durable named asset next to the template's other files, e.g. `viral-dances/<slug>/character.png`, so a future "reuse / re-drive this character" is a single URL — no frame-grabbing from the lossy output video.
- This is the durable counterpart to [[reference_mobile_preview_bitrate_streaming]] (which already says never delete by filename); the character image deserves the same treatment as `driving_video.mp4` / `preview_stream.mp4`. Relates to the no-overfit boundary in [[feedback_no_overfit_prompts]] (the bespoke prompt is throwaway, but its *output* — the approved character — is not).
