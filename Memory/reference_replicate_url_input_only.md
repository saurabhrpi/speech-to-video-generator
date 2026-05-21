---
name: replicate-url-input-only
description: Replicate's local file-upload path (passing an open file handle to replicate.run) silently fails for some models — pre-upload to a public URL and pass that instead. Misleading error is "Cog: Got error trying to upload output files".
metadata:
  type: reference
---

When calling `replicate.run(...)` from Python, the SDK supports two ways to pass a file input:

- **Local file handle**: `input={"video_path": open("clip.mp4", "rb"), ...}`
- **Public URL**: `input={"video_path": "https://.../clip.mp4", ...}`

Verified S70 on `lucataco/real-esrgan-video:3e56ce4b...`: the local-handle path **failed twice in a row** in 3-5s with no logs and the misleading error `"Cog: Got error trying to upload output files"`. Same input passed as the R2 public URL ran end-to-end in ~226s and returned a valid 1080×1920 mp4.

**Why:** The SDK uploads the file to Replicate's own `/v1/files` host, then passes that internal URL to the model worker. Some model workers can't fetch from that internal host (likely a VPC/scoping issue between Replicate's storage tier and the GPU runners). The error message is misleading — it surfaces at the *output* upload stage, but the root cause is *input* fetch failure that crashes the model immediately.

**How to apply:**

- Default to passing public URLs for any file-typed input on Replicate models.
- If you don't have a public host handy, upload to R2 first via `scripts/upload_template_assets.py` (or `r2_client.upload_file` to the public templates bucket), then pass the resulting `assets.speech-2-video.ai/...` URL.
- If you see the "Cog: Got error trying to upload output files" error with a sub-10s `predict_time` and empty logs, **don't trust the error message** — switch to URL input before debugging output handling.
- `scripts/upscale_driving_video.py` is hardened to require `--input` to be `http(s)://`. Don't relax that without re-verifying.
- The same workaround likely applies to other Replicate models; check before assuming local-file upload works.
