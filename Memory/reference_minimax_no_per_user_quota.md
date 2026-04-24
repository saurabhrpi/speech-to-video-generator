---
name: MiniMax has no sub-accounts / per-user quotas / programmatic keys
description: MiniMax developer platform exposes no primitives to enforce per-end-user limits upstream. If you need per-user gating, do it in your own backend — don't wait for MiniMax.
type: reference
---

Researched S50 when considering whether to mint a MiniMax "temp sub-account with 5 credits" per anon app user so that MiniMax would naturally reject concurrent-submit abuse upstream. Answer: **MiniMax cannot backstop per-user enforcement for us.**

**What MiniMax does NOT expose (as of 2026-04 platform docs):**
- **No programmatic sub-account / child-key creation.** API key creation is a manual dashboard action at `platform.minimax.io/user-center/basic-information/interface-key`. No REST endpoint to mint keys from code.
- **No per-user quotas or rate limits.** Limits are account-wide and tier-based (e.g. 100 RPM free, up to 500 RPM burst on paid). No API to say "this key may spend 5 credits".
- **No usage groups / projects / partner / reseller APIs.** `GroupId` exists but is a single account-level identifier; not a per-user boundary. No documented organization-management API.

**What MiniMax DOES do:**
- **Synchronous insufficient-balance rejection at submit.** `POST /v1/video_generation` returns error code `1008` "insufficient balance" on the submit response itself — a single-request gate works. But atomicity under concurrent submits against the SAME balance is not documented — treat as unspecified.

**Implication:** From MiniMax's perspective, our entire app is a single tenant with one key and one balance. Any per-end-user gating MUST live in our backend (or be delegated to a different aggregator entirely — AIMLAPI, Replicate, fal.ai, Together may expose per-user key APIs; would need re-verification per vendor).

**Source URLs (verify before acting in a future session, in case docs evolve):**
- `https://platform.minimax.io/docs/api-reference/api-overview`
- `https://platform.minimax.io/docs/api-reference/video-generation-t2v`
- `https://platform.minimax.io/docs/api-reference/errorcode`
- `https://platform.minimax.io/docs/token-plan/faq`

**If upstream enforcement is ever business-critical:** email MiniMax sales/support — enterprise features may exist but are undocumented.
