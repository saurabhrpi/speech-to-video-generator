---
name: expo-av mounts a live AVPlayer per <Video> (shouldPlay=false ≠ freed)
description: Every MOUNTED expo-av <Video> holds an iOS AVPlayer/decoder regardless of shouldPlay; too many mounted = all videos (even visible ones / the hero) render black. Gate by MOUNTING + a first-frame poster.
type: reference
---

expo-av instantiates a live AVPlayer (hardware decode session) for EVERY mounted
`<Video>`, **even with `shouldPlay={false}`** — pausing does NOT free the
decoder. Past iOS's concurrent hardware-decode ceiling (~a handful), AVPlayers
can't acquire a pipeline and render a FROZEN/BLACK frame. The failure is
**global and nondeterministic** (whichever players win the decode race play, the
rest go black — including fully-visible tiles and the hero, whose code was
untouched), and it is **NOT** network and **NOT** a wedged sim (survives R2
HTTP-200 checks AND a full simulator reboot).

S80 cost: a long debug. A non-virtualized `ScrollView` home grid mounted ~20 tile
`<Video>`s + the hero at once → all black. Gating `shouldPlay` alone did NOT fix
it (players stayed mounted). Diagnosis tell: the hero (untouched) was also black.

Fix (both parts, = the competitor's home-grid behavior):
1. **Mount the `<Video>` only while the tile is visible** (conditional render —
   not just `shouldPlay`) so the live-player count is bounded to what's on
   screen. A fresh mount also auto-restarts from frame 0 (TikTok restart; no
   `replayAsync`). Use a vertical `FlatList` (virtualizes rows) + per-row and
   per-tile viewability to drive `isVisible` (`rowOnScreen && withinRowVisible`).
2. **First-frame poster `<Image>`** as the always-present base layer so a
   non-playing tile shows its first frame instead of black ("paused = first
   frame"). Generate per template: frame 0 → `thumbnail.jpg` → Firestore
   `assets.thumbnail_url`. Script: `scripts/generate_template_thumbnails.py`.

Overwriting an existing R2 `thumbnail.jpg` hits the immutable-cache trap
([[reference_r2_immutable_cache_same_key_overwrite]]) AND the app's NSURLCache —
append a `?v=N` cache-buster to the Firestore `thumbnail_url` so the device
refetches. A brand-new key (or a changed URL, e.g. placeholder→canonical) needs
no buster.

Migration note: expo-av is deprecated (removed in SDK 54); `expo-video`
(`useVideoPlayer`) has explicit player-lifecycle control and would make this
decoder-bounding cleaner.
