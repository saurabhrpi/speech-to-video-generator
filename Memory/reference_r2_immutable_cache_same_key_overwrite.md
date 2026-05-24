---
name: R2 immutable-cache stale on same-key overwrite
description: Overwriting an R2/CF asset at the same key serves a STALE copy to browsers that previously loaded that URL — cache-control is immutable+1yr, so the browser never revalidates. Fresh fetchers (curl/ffmpeg/Kling) see the new file; the browser lies.
type: reference
---

R2 assets are served with `cache-control: public, max-age=31536000, immutable` (see CLAUDE.md R2 section — "1y immutable"). The `immutable` directive tells **browsers** never to revalidate within the year.

**The footgun:** when we iterate on a template asset and re-upload to the **same key** (e.g. `viral-dances/<slug>/driving_video.mp4`), any browser that loaded that URL before the overwrite keeps serving the **old** cached copy from local disk — indefinitely. The origin has the new file; the browser shows the old one.

**Symptom (S76, DPWM driver):** user's Chrome showed the driving video as `0:15` total duration; ffmpeg/curl/atom-parse of a fresh download all showed 16.87s (mvhd/tkhd/mdhd all ~16.87s, no 15s anywhere), and Kling — fetching fresh — produced a 16.80s output. The browser was showing a stale 15s version cached before the recovered 16.87s re-upload.

**Note:** `cf-cache-status: DYNAMIC` does NOT mean "no caching" — it only means the CDN *edge* isn't caching. The *browser* still honors `immutable`.

**Fix (verified S76):** hard-refresh the tab (⌘⇧R) — clears it instantly. (cache-bust query `?v=N` or incognito also work.) `curl`/ffmpeg/Kling never use the browser cache so they always see origin.

**Do NOT** work around this by versioning/content-addressing asset keys — user directive S76: keys stay stable, the canonical asset URL is fixed, and overwriting it is fine because fresh fetchers (and a hard-refresh) get the new file. The browser stale-cache is a non-issue once you ⌘⇧R. When a teammate reports "the asset looks like the old version," suspect browser cache before suspecting the upload. Related: [[reference_cf_r2_custom_domain_needs_cache_rule]], [[reference_firestore_partial_update_etag]] (same class — stale-read via caching layer).
