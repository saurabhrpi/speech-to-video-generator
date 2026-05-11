---
name: GCP Vertex AI rebranded to "Agent Platform" (display only)
description: As of ~April 2026, the GCP API Library shows "Agent Platform API" instead of "Vertex AI API" — but service name is still aiplatform.googleapis.com and SDK behavior is unchanged
type: reference
---

In the GCP Console API Library, the product card formerly titled **"Vertex AI API"** is now titled **"Agent Platform API"** (Google Enterprise API). This caused confusion in S62 — searching "Vertex AI" in the API Library only surfaced unrelated retail products like "Vertex AI Search for commerce".

**Confirmation it's the same API:** the Product Details page shows `Service name: aiplatform.googleapis.com` at the bottom. That's the canonical Vertex AI service identifier — unchanged.

**What's affected:**
- GCP Console product card title: changed
- API Library search behavior: searching "Vertex AI" no longer matches; search `aiplatform` or use direct URL instead
- Underlying service + endpoints: unchanged
- `google-genai` SDK in Vertex mode: unchanged
- IAM role **display names**: rebranded too. `roles/aiplatform.user` now displays as **"Agent Platform User"** (was "Vertex AI User"). Confirmed S62. Search by role ID (`aiplatform.user`) or new display name ("Agent Platform").
- IAM role IDs (`roles/aiplatform.user`, `roles/aiplatform.admin`, etc.): unchanged
- Quotas page: still under "aiplatform" prefix
- "Vertex AI Service Agent" (`roles/aiplatform.serviceAgent`) is a different thing — Google's auto-managed internal identity that gets created when the API is enabled. Do NOT grant this to user-created SAs.

**Direct URL that works regardless of rename:**
`https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=<PROJECT_ID>`

**Verified S62 (2026-05-10).** Enabled on the `speech-2-video` project; the click-Enable action turns on `aiplatform.googleapis.com` exactly as before.
