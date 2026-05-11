---
name: CF R2 token result screen does not show Account ID
description: When creating an R2 API token in the Cloudflare dashboard, the result screen shows the native bearer token + S3 access_key + secret, but the Cloudflare Account ID needed for boto3's S3 endpoint URL is found elsewhere (Account Home sidebar, or derived from the S3 endpoint URL also on the screen)
type: reference
---

When creating an R2 API token via Cloudflare dashboard, the post-creation result screen surfaces three credentials, NOT four:

- **Token value** — Bearer token for the native R2 binding API (Workers etc.). NOT used by boto3 / S3-compatible clients.
- **Access Key ID** — for S3 API. Used by boto3 as `aws_access_key_id`.
- **Secret Access Key** — for S3 API. Used by boto3 as `aws_secret_access_key`.

The **Cloudflare Account ID** (needed to construct the S3 endpoint URL `https://<account_id>.r2.cloudflarestorage.com`) is NOT on the token result screen. Find it:

1. The same token result page often displays the full S3 endpoint URL nearby — the long-hex subdomain IS the account ID. Copy it from there.
2. Cloudflare dashboard → click your account name → **Account Home** → right sidebar → "Account ID" with a copy icon.
3. R2 home page → "Use S3 API" section → endpoint URL.

**Verified S61 (2026-05-10):** User created the first R2 token; result screen showed token + access_key + secret but no field labeled "account_id". Earlier instruction to "save the 4 secrets shown ONCE" was misleading; only 3 are on that screen.
