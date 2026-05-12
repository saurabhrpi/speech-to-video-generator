---
name: Cloudflare R2 API tokens are bucket-scoped — expand scope when adding buckets
description: R2 API tokens default to single-bucket scope; presigning / reading from a NEW bucket with an old token returns 403. Always re-check token scope when adding a new R2 bucket; either edit the existing token to include both buckets or create a new one with broader scope.
type: reference
---

When creating an R2 API token via Cloudflare dashboard, the default scope is **a specific bucket** (the one you select during token creation). If you later add a second bucket and try to use the SAME token to sign URLs / read / write against it, you'll get a **403 Forbidden** with no useful body.

**Symptom signature:**
- Presigned GET URL returns `HTTP/1.1 403 Forbidden` with `Server: cloudflare`, no body content
- The same token works fine on the original bucket (proves auth itself isn't broken)
- Presigning code itself is correct (boto3 just signs locally; R2 enforces at request time)

**Quick diagnostic** (Python):
```python
from src.speech_to_video.utils import r2_client
from src.speech_to_video.utils.config import get_settings
import subprocess
s = get_settings()
for label, bucket, key in [
    ('OLD',  s.r2_bucket, 'known-existing-key'),
    ('NEW',  s.r2_selfies_bucket, 'fixture-key'),
]:
    url = r2_client.generate_presigned_get_url(key, bucket=bucket, expires_in=300)
    r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', url], capture_output=True, text=True)
    print(f'{label}  bucket={bucket}  status={r.stdout}')
```
If OLD = 200 and NEW = 403 → confirmed bucket-scope issue.

**Fix paths:**
1. **Edit existing token** in CF dashboard → R2 → Manage API Tokens. Change scope from "single bucket" to either "specific buckets" (multi-select) or "all buckets in this account." Saving may rotate the access_key/secret — be ready to update `.env` + any prod secret stores (Replit Deployment Secrets etc.).
2. **Create new token** with broader scope, replace env vars, delete the old one.

**Trade-off** between the two scope choices:
- "Specific buckets" — least privilege; revoke or re-scope per bucket. Operational friction every time a bucket is added.
- "All buckets in this account" — broader blast radius if leaked, but zero operational friction. Probably the right pick for a small team where adding buckets is common.

**Verified S62 (2026-05-12).** S61 token was scoped to `speech-to-video-templates` only. Adding `speech-to-video-selfies` for AIV-89/AIV-14 broke presign with 403. Fix: expand token scope.
