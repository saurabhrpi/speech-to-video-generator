---
name: kling-audio-lead-and-preview-propagation
description: Kling MC (pro+video, both v2.6 AND v3) outputs 30fps and the audio LEADS video by ~0.5s (lyrics heard before lips move). Fix = +0.5s -itsoffset audio delay on the OUTPUT (confirmed DPWM S75+S76). Root cause is INSIDE Kling, not the driver — re-encoding driver to clean CFR + flattening edit lists + removing VFR did NOT help (S76). Preview-as-driver propagation still unverified.
metadata:
  type: feedback
---

**Confirmed (S75 + S76, DPWM) — Kling MC `mode=pro` + `character_orientation=video`, on BOTH `kling-v2-6` and `kling-v3`:** output is 30 fps regardless of driver framerate, and the audio **leads** the video — you hear the lyrics first, the lips/motion follow by ~0.5s. A **+0.5s audio delay on the OUTPUT** fixes it, confirmed by the user on DPWM in two separate sessions.

Fix (stream-copy, no re-encode, no quality loss):
```
ffmpeg -i in.mp4 -itsoffset 0.5 -i in.mp4 -map 0:v:0 -map 1:a:0 -c copy -shortest out.mp4
```
Input 0 = video (no offset); input 1 = the same file's audio, delayed +0.5s. "Audio leads" (lyrics before lips) → delay the audio so it lands on the lips. Side effect: ~0.5s leading silence + ~0.5s lost off the tail (cosmetic — clean up head/tail after locking magnitude if it matters). Exact magnitude can only be judged by ear — bracket (e.g. 0.40/0.50/0.60) and let the user pick; 0.50 has been the answer for DPWM both sessions.

**Root cause is INSIDE Kling, NOT the driver — input-timeline hypothesis REJECTED (S76).** We tested the theory that the driver's messy container timing caused the lead: re-encoded the DPWM driver to clean **30fps CFR**, flattened its 2-entry video **edit list** (a 16ms empty-edit + content offset), and removed **VFR** (43.86fps → 30 CFR), re-uploaded to the same R2 key, regenerated. **Sync was unchanged.** Separately, switching `v2.6 → v3` also did **not** help sync (it only delivered faster, ~395s vs ~467s). Conclusions:
- Don't CFR-clean / edit-list-flatten drivers expecting a sync fix — wasted effort.
- Don't flip model version expecting a sync fix.
- The lead is produced by Kling's own processing/mux. The ONLY working fix is the output-side `-itsoffset`. Exact internal mechanism still unknown, but the driver input is ruled out — so don't re-litigate the driver.

**Propagation (preview-as-driver) — S76 data point: runtime came out SYNCED.** A real DPWM runtime gen (v2.6-**std** + preview-as-driver, with the +0.5s-corrected preview as the driver) had NO audio lead — no runtime fix needed for this gen. AIV-105 is kept OPEN (not closed): this is the FIRST confirmation, and we're gathering several more cross-template confirmations before concluding the runtime fix is unnecessary. Two candidate explanations, not disambiguated from one data point: (a) the preview audio-correction propagates through to runtime, OR (b) the lead is a PRO-mode artifact and v2.6-**std** simply doesn't introduce it (the lead was only ever confirmed on v2.6-pro S75 and v3-pro S76; std was never tested before). Practically: under the current operating model (global v2.6-std runtime + preview-as-driver + audio-corrected previews), runtime gens are clean. Re-verify if a future template shows a runtime lead despite a corrected preview, or if global runtime flips to pro.

**How to apply:**
- Audio leads (lyrics before lips) on a Kling MC output → `-itsoffset 0.5` delay on the output, stream-copy. Bracket the magnitude by ear if 0.5 isn't perfect.
- Don't waste a Kling gen on driver CFR-cleanup or a model-version flip hoping to fix sync — neither does.
- Runtime gens under v2.6-std + preview-as-driver looked clean on the FIRST check (S76 DPWM) — but AIV-105 stays open pending more cross-template confirmations before concluding no per-template runtime shift is needed. Re-verify especially if global runtime flips to pro.

See also: [[no-force-15s-trim]] (adjacent driver lesson, same debugging line), [[video-motion-needs-human-eye]] (sync/motion is judged by a human, not by metadata/frame probes).
