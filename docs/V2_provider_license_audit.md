# V2 AI-Generation Provider License Audit

**Audit date:** 2026-05-07 (S59).
**Use case:** AI-generated T2V/T2I outputs hosted on Cloudflare R2, fed as reference inputs to Kling 2.6 Motion Control, embedded in a paid mobile app sold via pay-as-you-go credits.
**Status:** Research output from a one-shot deep audit. Recommendations below are load-bearing — but the **two unblockers** at the bottom are gating before any asset goes live in production.

---

## Master comparison

| Provider | A. Commercial OK? | B. Self-host OK? | C. Input to other AI OK? | D. Sold downstream OK? | E. Attribution? | F. Notable content restrictions | G. Indemnified? | H. Termination risk |
|---|---|---|---|---|---|---|---|---|
| **Veo 3.1 (Vertex AI / Gemini API paid)** | ✅ Paid tier OK; "for professional/business purposes" [1] | ✅ Not restricted [1] | ⚠️ Ambiguous — "may not develop models that compete with the Services" [1]; using as Kling input is *not* model development | ✅ Paid tier permits | ⚠️ **SynthID watermark mandatory & non-disableable** [4][6] | Standard (no real-people, NSFW, copyright) | ✅ Yes — Generated Output Indemnity covers Imagen, plans to extend to Veo at GA [5] | Low — enterprise terms |
| **Kling T2V (kling/kuaishou direct API)** | ✅ Paid + Enterprise API tier permitted [9][10] | ⚠️ **License requires "Kling AI" brand/logo on shared video unless waived in writing** [9] | ❌ Likely problematic — Kuaishou ToS grants *them* training rights on inputs/outputs | ⚠️ Yes if branded; without brand, written permission required | ❌ Brand/logo required per [9] | Standard | ❌ No indemnity | ⚠️ Medium — enterprise contract required for API |
| **OpenAI Sora 2 (API)** | ✅ Yes — "you own the Output" [11][12] | ✅ Yes (you own output) | ⚠️ Business Terms restrict using Output to develop models that *compete with* OpenAI | ✅ Yes per Business Terms | ❌ **C2PA metadata embedded; OpenAI says "do not remove"** [3]; visible watermark on non-Pro | Post-Oct 2025 "opt-in" copyright policy: prohibits unauthorized IP, no real-people likenesses without consent [2][7] | ✅ Customer Copyright Commitment for API customers covers third-party IP claims [12] | Low — Business Terms |
| **MiniMax Hailuo (direct API)** | ✅ Paid — user retains IP, commercial permitted [13] | ✅ Not restricted [13] | ⚠️ Not addressed — no explicit prohibition | ✅ Yes | ⚠️ Not specified in API ToS; consumer app embeds visible watermark — verify direct API path | Standard prohibitions [14] | ❌ No indemnity; user indemnifies MiniMax | ⚠️ Medium — Chinese-jurisdiction provider |
| **Pixverse (platform API, Jan 5 2025 ToS)** | ✅ §5.3: "use of AI-generated content for commercial purposes is not restricted" [16] | ✅ Not restricted [16] | ❌ §3.3(5) prohibits using service to "develop, train, or improve other algorithms, models" with "competitive relationships" [16] — Kling not a competitor, defensible | ✅ Yes [16] | ⚠️ §3.3(8): "shall not tamper with or delete identifiers indicating content is AI-generated" [16] | Standard 10-category prohibitions [16] | ❌ User indemnifies Pixverse [16] | Low |
| **Seedance (ByteDance, official 1.5 ToS)** | ⚠️ "Commercial use of generated videos may be subject to additional terms" — not unconditional [17] | ✅ User retains rights [17] | ⚠️ Not addressed | ⚠️ Conditional — see (A) | ⚠️ Not specified | ⚠️ **Active Hollywood C&D situation (Feb 2026): Disney, Netflix, Paramount sent legal notices over Seedance 2.0 generating recognizable IP** [18][19] | ❌ No indemnity | ❌ **High** — IP storm; legal exposure unresolved |
| **Imagen 4 / Nano Banana Pro (Vertex AI / Gemini paid)** | ✅ Paid tier OK [1] | ✅ Not restricted [1] | ⚠️ Same "no competing models" clause as Veo; reference-asset use defensible [1] | ✅ Yes | ⚠️ **SynthID watermark embedded — mandatory, non-removable** [4][5] | Standard | ✅ Yes — Imagen explicitly listed in Google's Generated Output Indemnity at GA [5][8] | Low |
| **OpenAI DALL-E 3 (API)** | ✅ Yes — "you own the Output" + "any legal purpose, including commercial" [12][20] | ✅ Yes | ⚠️ Same competing-model clause as Sora [12] | ✅ Yes | None mandated for image API today | Standard usage policies | ✅ Customer Copyright Commitment [12] | ❌ **DALL-E 3 retires from API May 12, 2026** [20] — replaced by GPT Image 1.5. **Migration required.** |
| **Black Forest Labs FLUX (direct API)** | ✅ Yes — outputs usable for personal/commercial [21] | ⚠️ §2(a): may not host an API endpoint to FLUX models or expose them to third parties [21] — does NOT prohibit hosting FLUX *outputs* | ❌ "May not use Output to train, distill or fine tune any other AI model that competes with FLUX" [21] — Kling not a FLUX competitor, defensible; flag for counsel | ✅ Yes | None mandated | Standard | ❌ No indemnity; **BFL retains perpetual royalty-free license to your inputs/outputs to train their own models** [21] | ⚠️ Medium — input-training clause |

---

## Per-provider notes

### Google (Veo 3.1 / Imagen 4 / Nano Banana Pro)
Cleanest license stack of the audit. **Indemnification is the killer feature** — Google is the only provider here offering Generated Output Indemnity for both training data and outputs (subject to "responsible AI practices" — content policy compliance). The catch: SynthID is mandatory and non-removable. Reference asset will be machine-detectable as AI-generated forever, and so will the downstream Kling clip if SynthID survives Kling's pipeline (it likely does — designed to survive re-encoding/cropping). For our use case this is acceptable: end users already know it's AI; the watermark is invisible. Do **not** misread the "may not develop competing models" clause — feeding Veo output into Kling Motion Control is reference-asset use, not training. Document our interpretation in case of audit.

### Kling T2V
Two real problems: (1) brand/logo display requirement on shared videos breaks our "user pays us for the clip" UX. We can ask for written waiver but that's an enterprise sales conversation. (2) Kuaishou's broad license to your content + their training rights creates a chain-of-custody concern when user selfies enter the pipeline. **Recommendation: only use Kling for the *Motion Control* leg (where we're already locked in), not for upstream T2V reference generation.**

### OpenAI Sora 2
Customer Copyright Commitment is a real indemnity (narrower than Google's but real). Post-Oct-2025 opt-in IP policy is fine for "original dance/action references" — we're not cloning Disney trends. C2PA metadata is the operational concern: must persist through R2 hosting (will — file unchanged) and through Kling Motion Control (Kling will likely strip it; Kling's choice, not our violation). Visible watermark applies to non-Pro outputs — verify API tier returns watermark-free output.

### MiniMax Hailuo
Already in our stack via `MiniMaxClient`. ToS silent on enough things (input-to-other-AI, watermark on direct API output) that we should treat it as "permissive but unverified" rather than "license-clean." Lowest-risk read because we own the output and there's no explicit anti-derivative clause, but no indemnity = we carry IP risk ourselves.

### Pixverse
Don't confuse with consumer site ToS (says non-commercial). Platform/API ToS [16] is unambiguous: §5.3 explicitly permits commercial use. §3.3(5) "no competing models" is narrower than FLUX's — bars *competing* model development, and Kling Motion Control is not a Pixverse competitor. §3.3(8) "do not delete AI-generated identifiers" workable as long as we don't actively strip metadata.

### Seedance
**Avoid for V2 launch.** Three reasons: (1) "commercial use may be subject to additional terms" — not the unconditional grant we need. (2) Active legal cease-and-desists from Disney/Netflix/Paramount over Seedance 2.0 generating recognizable IP. Even if our prompts are clean, association risk is real if provider tightens output policies mid-flight. (3) No indemnity. Quality argument doesn't survive legal-risk argument.

### DALL-E 3
**Migration required: API retires May 12 2026** — 5 days from audit. Use GPT Image 1.5 instead. Same OpenAI Business Terms, same Customer Copyright Commitment. Do not build new pipelines on DALL-E 3.

### FLUX (BFL API)
The "no host an API endpoint to FLUX" clause [§2(a)] does **not** prohibit hosting FLUX *outputs* on R2 — bars proxying the model itself. Output hosting is fine. Two real issues: (1) BFL retains perpetual royalty-free license to inputs and outputs to train their own models — if we ever pass user selfies to FLUX, those go into BFL training. (2) "may not use Output to train models that compete with FLUX" — Kling Motion Control is video, FLUX is image, no competition; defensible. No indemnity is the bigger concern.

---

## Launch recommendation (S59-locked)

### T2V reference video for V2 — primary: **Veo 3.1**. Backup: **Hailuo 2.3**.

**Veo 3.1 wins on three dimensions:**
- **Indemnification** — only T2V provider in the audit offering it.
- **Licensing clarity** — paid Vertex tier explicitly permits commercial + self-host.
- **Quality** — 10s 720p+ with cinematic motion is its sweet spot.

Mandatory SynthID is acceptable — invisible to users, our app already discloses AI generation.

**Hailuo 2.3 as backup** because already integrated, ToS permissive on output ownership, complements Veo on cute-animal/casual-impulse content. No indemnity is the trade-off; mitigate by being conservative on prompts (no real people, no IP).

**Rejected:**
- **Kling T2V** — brand/logo display requirement breaks UX.
- **Sora 2** — C2PA metadata adds maintenance burden + opt-in IP policy restrictive for trend-recreation.
- **Pixverse** — acceptable but no upside vs Veo.
- **Seedance** — active Hollywood litigation; avoid.

### T2I reference image for V2 — primary: **Nano Banana Pro (Imagen 4 family)**. Backup: **GPT Image 1.5** (post-DALL-E-3 retirement).

**Nano Banana Pro wins because:**
- Already in our codebase (`google/nano-banana-pro-edit` for paused Timelapse pipeline).
- Same Vertex AI license stack as Veo: indemnified, commercial-clean, paid-tier permissive.
- Photorealistic + selfie-composition-friendly.
- SynthID mandatory but invisible.

**GPT Image 1.5 as backup** once DALL-E 3 retires May 12 — covered by Customer Copyright Commitment, owns-output language.

**Rejected:**
- **FLUX** — BFL's input-training clause + no-indemnity is a worse trade than Nano Banana Pro at our scale (~25 reference assets pre-launch).

---

## Pre-launch unblocker (one — hard gate)

**Per-asset IP / likeness audit before R2 upload.** Every generated reference asset (T2V dance video or T2I scene image) is reviewed before going live in production for:
- Incidental real-people likeness — a face or body that could plausibly be identified as a specific real person.
- Recognizable IP — Disney/Marvel/Pixar/anime/branded characters, recognizable film stills, copyrighted choreography, brand logos, identifiable copyrighted music in the audio bed.
- Trade dress on costuming or scene composition that copies a specific creator's signature look.

Found violations get the asset regenerated with adjusted prompts, never published as-is. **This is the only hard legal gate for V2 launch.** Google's Generated Output Indemnity (and OpenAI's Customer Copyright Commitment, where applicable) carve out cases of intentional infringement; our liability shield depends entirely on responsible-use compliance at this gate.

Operationalized as a manual review step in the asset-generation pipeline (Track 1 backend work). No template flips to `published_status: true` without the gate passing.

---

## Vendor indemnity self-interpretation memo (S59)

> **Why this section exists.** The original audit flagged a second unblocker — getting Google legal/sales to confirm in writing that our Veo/Imagen → Kling Motion Control reference-frame chain stays within the Vertex AI Generated Output Indemnity scope. That ask was deprioritized S59 (see decision below). This memo self-documents our interpretation so a future legal review, audit, or due-diligence pass can see we considered it deliberately, not by oversight.

**Decision (S59):** Deprioritize the written-confirmation request to Google. Operate on the published indemnity terms. Revisit post-launch if (a) revenue/scale justifies vendor-legal cycles, or (b) an IP claim is filed against us.

**Reasoning:**
- IP claim probability is low at our stage given the responsible-use practices documented above (no real people, no recognizable IP, conservative prompts, manual per-asset audit).
- Vendor-legal turnaround on the request would likely take days to weeks and could miss V2 launch.
- Without written confirmation, the indemnity still exists in the published terms — we just argue scope from first principles if a claim is filed. Defensible, just harder than waving a vendor email.
- The cost asymmetry favors moving fast: writing buys evidentiary cover for a scenario that probably never happens; not writing accepts marginal residual risk.

**Our interpretation of indemnified scope (the argument we'd make if a claim came):**

The chain we run: text prompt → Veo/Imagen output (T2V or T2I asset) → hosted on Cloudflare R2 → fed as `image_url` / reference frame to Kling 2.6 Motion Control alongside an end-user selfie → Kling produces a final clip → user pays us in pay-as-you-go credits for the final clip.

Three points support this being within the Generated Output Indemnity:

1. **The Veo/Imagen output itself is the indemnified Output.** Google's terms indemnify Output of indemnified services. Hosting that Output on our infrastructure and incorporating it into a downstream commercial product is what the paid Vertex tier expressly permits ("for professional/business purposes"). The Output's identity as Veo/Imagen content is preserved at every step we control.
2. **Use as reference-frame input to Kling Motion Control is reference-asset use, not model development.** The Vertex terms restrict using Output to "develop models that compete with the Services." Kling Motion Control is a third-party generative model we're consuming, not training, fine-tuning, or developing. We are not using Veo Output as training data. We're using it as a runtime input to an unrelated provider's service — closer to embedding a stock asset in a downstream product than to model R&D.
3. **SynthID provenance is preserved on our side of the chain.** SynthID is embedded in the Veo/Imagen Output and we do not actively strip or tamper with it on R2. Whether Kling Motion Control's pipeline preserves or strips SynthID downstream is Kling's behavior, outside our control. We comply with the responsible-AI practices the indemnity is conditioned on.

**Risks acknowledged:**
- Google could argue the *final clip* (the Kling-Motion-Control output) is no longer a Veo/Imagen Output and therefore outside indemnified scope. Our counterargument: the alleged-infringing element traces back to the Veo/Imagen Output that we used as reference; the indemnity attaches to the upstream Output, and the downstream transformation doesn't sever the chain.
- A specific claim might focus on choreography or scene composition that the Veo/Imagen prompt didn't intend but the model produced. Mitigation: per-asset audit gate above catches recognizable IP before publishing.
- The indemnity carves out intentional infringement and material breach of usage policies — both fully within our control via the per-asset audit gate.

**Trigger for revisiting this memo:** any of (a) first IP claim filed against us, (b) Google materially changes the Vertex AI indemnity terms, (c) revenue >$X/month threshold where vendor-legal cycles are worth it, (d) M&A / fundraise due-diligence asks for vendor confirmations.

**Memo author:** Saurabh Sharma (V2 product lead). **Memo date:** 2026-05-07.

---

## Sources

- [1] Gemini API Additional Terms (Mar 23 2026): https://ai.google.dev/gemini-api/terms
- [2] Sora 2 commercial license guide / OpenAI launch posts (Oct 2025+): https://openai.com/index/launching-sora-responsibly/
- [3] OpenAI: Creating with Sora safely (C2PA metadata): https://openai.com/index/creating-with-sora-safely/
- [4] Veo / SynthID — Google Cloud Vertex AI announcement: https://cloud.google.com/blog/products/ai-machine-learning/introducing-veo-and-imagen-3-on-vertex-ai
- [5] Google Cloud: Protecting customers with generative AI indemnification: https://cloud.google.com/blog/products/ai-machine-learning/protecting-customers-with-generative-ai-indemnification
- [6] SynthID Veo 3.1 — non-optional at all tiers: https://www.aifreeapi.com/en/posts/veo-3-1-watermarks-synthid
- [7] OpenAI Sora opt-in copyright policy (Oct 3 2025): https://openai.com/policies/usage-policies/
- [8] Google Cloud Generative AI Indemnified Services list: https://cloud.google.com/terms/generative-ai-indemnified-services
- [9] Kling AI Terms of API Paid Service: https://app.klingai.com/global/dev/document-api/protocols/paidServiceProtocol
- [10] Kling AI commercial-use guide 2026: https://www.glbgpt.com/hub/can-i-use-kling-ai-for-commercial-use/
- [11] OpenAI: Will OpenAI claim copyright over API outputs?: https://help.openai.com/en/articles/5008634-will-openai-claim-copyright-over-what-outputs-i-generate-with-the-api
- [12] OpenAI Business Terms — May 2025: https://openai.com/policies/may-2025-business-terms/
- [13] Hailuo AI Video / MiniMax commercial-licensing notes: https://hailuoai.video/pages/knowledge/ai-product-media-commercial-licensing
- [14] Hailuo AI Video Terms of Service (Nov 25 2024): https://hailuoai.video/doc/terms-of-service.html
- [15] Pixverse consumer Terms of Service (non-commercial default): https://pixverse.ai/en/terms-of-service
- [16] Pixverse Platform (API) Terms of Service (Jan 5 2025): https://pixverse.ai/en/pixverse-platform-terms-of-service/
- [17] Seedance 1.5 Pro Terms: https://www.seedance15.net/terms
- [18] MPA / Disney / Netflix C&D over Seedance 2.0 (Feb 2026): https://www.hollywoodreporter.com/business/business-news/mpa-cease-and-desist-bytedance-seedance-2-0-1236510957/
- [19] ByteDance pledges Seedance 2.0 safeguards (Feb 16 2026): https://www.cnbc.com/2026/02/16/bytedance-safegaurds-seedance-ai-copyright-disney-mpa-netflix-paramount-sony-universal.html
- [20] Terms.Law DALL-E 3 commercial rights & retirement notice: https://terms.law/ai-output-rights/dall-e/
- [21] FLUX API Service Terms (May 29 2025): https://bfl.ai/legal/flux-api-service-terms
