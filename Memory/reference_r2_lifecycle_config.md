---
name: reference_r2_lifecycle_config
description: Setting R2 object-lifecycle (expiry) rules — needs an admin-scoped token, Filter.Prefix not legacy Prefix, no empty Filter
metadata:
  type: reference
---

Quirks of setting R2 bucket object-lifecycle (auto-expiry) rules — each cost real debugging time (S85). Tool: `scripts/set_r2_selfie_lifecycle.py`.

- **The app's R2 token is object-scoped** (GetObject/PutObject/Delete/List) and **cannot read or write bucket lifecycle config** → `AccessDenied` on Get/PutBucketLifecycleConfiguration. Use an **admin-scoped R2 API token** (Cloudflare → R2 → Manage R2 API Tokens → **Admin Read & Write**). The script reads it from `R2_ADMIN_ACCESS_KEY_ID` / `R2_ADMIN_SECRET_ACCESS_KEY` (dedicated env vars, NOT the app token — and `config.py`'s `load_dotenv(override=True)` would clobber inline `R2_*` that exist in `.env`, so the admin vars are deliberately separate). Revoke the admin token after use.
- **R2 scopes by the modern `Filter.Prefix` and SILENTLY DROPS a legacy top-level `Prefix`.** PUTting `{"Prefix": "selfies/", ...}` succeeds with no error but stores a prefix-LESS whole-bucket rule (verified by GET round-trip). Always use `{"Filter": {"Prefix": "selfies/"}, ...}`.
- **An empty `Filter: {}` → `MalformedXML`.** R2's own bucket-wide rules (e.g. the "Default Multipart Abort Rule") come back from GET with NO Filter/Prefix; keep those **verbatim**, never normalize them to `{}`.
- `put_bucket_lifecycle_configuration` REPLACES the entire config. Merge: keep unmanaged rules verbatim, dedup managed ones by rule **ID** (any expiry-days variant) **and** prefix.
- All three face-data input prefixes live in the one private `r2_selfies_bucket`: `selfies/`, `nbp-regen/`, `composites/`. Current prod state (S85): 1-day expiry on all three + the 7-day multipart-abort rule.
- **The bucket previously had NO object-expiry rule at all** — the "30d auto-delete on selfies/" claim in old `server.py` comments was never actually present, so inputs were retained indefinitely. The inline purge in `video_service._dispatch_motion_transfer` (delete-on-terminal) + this 1-day lifecycle backstop are what make the "deleted within 24h" privacy promise true.

Related: [[reference_r2_tokens_bucket_scoped]], [[reference_cf_r2_custom_domain_needs_cache_rule]].
