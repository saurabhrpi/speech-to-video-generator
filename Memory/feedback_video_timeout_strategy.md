---
name: VideoPlayer timeout strategy
description: Don't use fixed short timeouts for video loading — verify URL first, then use generous safety net
type: feedback
---

Fixed short timeouts (15s, 30s) for video loading are fragile — they conflate bad URLs with slow CDNs. A 15s timeout caused false "timed out" errors when CDN was just slow.

**Why:** Video generation costs real credits. A false timeout means the user sees an error even though the video was successfully generated — credits wasted, bad UX.

**How to apply:** Verify the URL is reachable first (GET with Range: bytes=0-0), fail instantly if bad. If reachable, use a generous safety-net timeout (90s) only to catch expo-av hangs — not CDN slowness.
