---
name: FastAPI returns 404 on HEAD for GET-only routes
description: `curl -I` against a FastAPI route registered with `@router.get(...)` returns 404 because Starlette doesn't auto-handle HEAD on GET routes. Use `curl -s` (GET) for reachability checks, not `curl -I` (HEAD).
type: reference
---

By default, FastAPI/Starlette routes registered with `@app.get(...)` or `@router.get(...)` only respond to GET. A HEAD request to the same path returns 404. This caught us verifying the Privacy Policy deploy on `https://speech-2-video.ai/privacy` post-republish — `curl -I` returned 404 even though the route was working perfectly via GET.

**Practical implication:** never use `curl -I` (HEAD) to sanity-check a FastAPI endpoint's reachability. Use `curl -s <url> | head` or `curl -sI -X GET <url>` (GET with headers-only output). Browsers and real clients (App Review, mobile fetches, etc.) issue GETs, so the 404 on HEAD is irrelevant in production.

**If you need HEAD support** (e.g., for a CDN or load balancer health check), explicitly add the method to the route decorator: `@router.api_route("/path", methods=["GET", "HEAD"])`. Don't ship this just to silence a `curl -I` warning — only add it when a real client actually needs HEAD.

Related routes that exhibit this behavior in our codebase: `/privacy`, `/terms`, `/support` (all in `src/speech_to_video/api/legal.py`).
