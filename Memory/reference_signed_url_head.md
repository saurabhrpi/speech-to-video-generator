---
name: Signed URLs reject HEAD requests
description: AIMLAPI CDN (Alibaba OSS) signed URLs are method-specific — HEAD returns 403, use GET with Range header instead
type: reference
---

AIMLAPI video URLs are signed for GET only (Alibaba Cloud OSS). Sending a HEAD request produces a 403 because the signature is computed with the HTTP method baked in — HEAD ≠ GET → signature mismatch → rejected.

**How to apply:** When verifying a signed CDN URL before loading, use `GET` with `Range: bytes=0-0` (fetches 1 byte) instead of HEAD. Accept both 200 and 206 (partial content) as success.
