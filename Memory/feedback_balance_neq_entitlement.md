---
name: Provider credits ≠ what you can actually spend
description: Provider's nominal/displayed credits can fail to fund the operation you want, via two distinct mechanisms — entitlement gating (same surface, wrong feature) and surface-split billing (different platform pool entirely). Probe before assuming.
type: feedback
---

When evaluating a paid AI-video provider, do NOT trust a credit balance as a signal of what you can actually generate. Two distinct failure modes to watch for:

**Mode A — Entitlement gating (same billing surface, wrong feature).** The displayed balance is real, but covers cheap operations (image gen, account ops) only. Expensive operations (video gen) require a different plan tier under the same account.

> Example — Higgsfield S57: `balance` returned `{credits: 10, plan: "free"}`, but every video gen failed with "Out of credits on free (null) plan." The 10 credits were image-only entitlement; video gen required Starter+. Wasted ~10 min diagnosing because the first error wording was a generic "Something went wrong" before clean plan-gating messages appeared.

**Mode B — Surface-split billing (entirely separate pool).** The provider has multiple billing surfaces (consumer site vs API platform vs enterprise) that share branding but have independent credit balances. Your consumer subscription doesn't fund API calls, even though both flow through the same provider.

> Example — Pollo S57: user had a paid Pollo consumer subscription. First gen rejected with "Not enough credits." Pollo's API platform docs explicitly state: *"API credits and user credits operate independently and are not interchangeable."* The consumer pool was funded; the API pool was empty.

**How to apply (before planning a spike around "we have N credits"):**
1. **Probe the actual surface you'll spend on.** Fire ONE smallest-possible probe gen via the exact code path / endpoint / key the spike will use. Don't trust dashboards from a different surface.
2. **Read error wording carefully.** "Plan gating" (Mode A) vs "Insufficient credits on this account" (Mode B) point to different fixes — upgrade tier vs top up the right pool.
3. **For multi-surface providers, ask the user which pool the credits are in.** Don't assume "user has a subscription" = "API key will work."
4. Don't let a displayed balance lull you into uploading assets, writing integration code, or making cost projections on the assumption credits = capability.
