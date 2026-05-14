---
name: Prefer direct-to-OG provider, but verify "middleman" claims first
description: User prefers direct API to the original model provider over wrappers (AIMLAPI, OpenRouter). BUT some "enterprise SKUs" (Vertex AI) are the OG provider's own door, not middlemen — verify before applying the rule.
type: feedback
---

User strongly prefers direct API access to the original model provider (Kling direct, Google direct) over thin-wrapper aggregators (AIMLAPI, OpenRouter, etc.). Locked S60 (2026-05-09); reasons clarified S62 (2026-05-11).

**Why — three roughly equal drivers, NOT just IP indemnity:**

1. **Cost.** Wrappers add markup on every call (often 10–30% over the OG provider's list price). At V2 launch volume this materially affects per-gen margin.
2. **Reliability of service.** Wrappers share rate limits, shared infrastructure, and a single point of failure across all their customers. OG providers give us our own quota lane and a more direct support escalation path. Past V1 incidents with AIMLAPI (intermittent timeouts, opaque error responses, no SLA) shaped this view.
3. **IP indemnity / license clarity.** You contract with the wrapper, not the model maker. For a consumer-facing V2 product where outputs may include recognizable people, scenes, or styles, enterprise IP indemnification (Vertex's Generated Output Indemnity, Kling's enterprise terms) is what stops a takedown / legal claim from landing on us.

   **Concrete risk scenarios indemnity covers:**
   - **Output reproduces copyrighted material.** Image-gen models occasionally regurgitate training data — a Disney character, a Pixar style, a Banksy. Rights-holder sues the *app that generated it*, not just the user.
   - **Training-data class-action spillover.** Active lawsuits against Stability/OpenAI/Midjourney from artists and Getty. If a court rules model output is derivative of training data, every past gen becomes retroactively exposed. Indemnity shifts that to Google.
   - **Style/character mimicry.** "In the style of [living artist]" or templates that look too close to a copyrighted scene/aesthetic. Style and likeness claims are increasingly litigated.
   - **DMCA / App Store takedown.** Rights-holder files DMCA → App Store can pull us within 24h. Indemnity doesn't prevent the takedown but gives legal teeth to push back instead of capitulating.

   **What indemnity does NOT cover (risk doesn't disappear entirely):**
   - User uploads someone else's selfie → publicity/privacy claim against us. Solved by consent checkbox + ToS, not by Google.
   - User violates ToS (CSAM, non-consensual deepfakes of real people) — indemnity voids.
   - Outputs we modify downstream past Google's response — depending on contract wording, edits may break coverage.

   Realistic blast radius: low per-gen probability, but single bad output × viral distribution × litigious rights-holder = existential for solo-founder app. Indemnity is cheap insurance, bundled into the Vertex SKU we're already paying for. Contract text: `cloud.google.com/terms/generative-ai-indemnified-services`.

Plus secondary factors: latency (extra hop), opacity (less control over auth / retry / features), and feature lag (wrappers expose a subset of the OG provider's capabilities, often months behind).

**How to apply:**
- For new V2+ provider integrations, default to direct API to the OG model maker
- For existing V1 integrations through wrappers, defer migration unless there's a forcing function
- Cite this preference when challenged on integration cost: "user-locked S60, no middlemen / hit OG providers directly"

**CRITICAL — verify what's actually a wrapper before applying the rule:**

Some "platform" SKUs from the OG provider itself are NOT wrappers. They are the OG provider's own enterprise door:

| Surface | What it actually is |
|---|---|
| AIMLAPI | Wrapper. Resells Kling, OpenAI, etc. SKIP for V2. |
| OpenRouter | Wrapper. SKIP. |
| **Vertex AI** | **Direct Google.** Same models as AI Studio. Enterprise SKU with IP indemnity (Generated Output Indemnity), GCP service account auth, data-residency controls. NOT a middleman. KEEP for V2. |
| Google AI Studio (`generativelanguage.googleapis.com`) | Direct Google. Consumer SKU. Simpler auth (API key) but NO IP indemnity. |
| Direct Kling API | Direct Kling. KEEP for V2. |

If the user asks "can we skip [layer]?" — investigate what the layer actually IS before agreeing. The "no middlemen" rule applies to wrappers (AIMLAPI), not to the OG provider's own enterprise SKU (Vertex). Confirmed S60 when user asked to drop Vertex, then reversed after seeing it's direct Google with IP indemnity.

**Reference:** `docs/V2_provider_license_audit.md` for the locked V2 provider stack:
- T2V: Veo 3.1 via Vertex AI (primary), Hailuo 2.3 via direct MiniMax (backup)
- T2I: Nano Banana Pro via Vertex AI (primary), GPT Image 1.5 (backup)
- Motion Control: Kling direct API (S60 user override of original AIMLAPI plan)
