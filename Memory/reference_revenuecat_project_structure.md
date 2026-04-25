---
name: RC Project = multiple Apps; offerings auto-link products by identifier
description: A RevenueCat Project contains multiple Apps (one per store/platform). Products are app-scoped, but offering packages can attach one product per app via the Edit-offering view's per-app dropdowns. Adding a product with the same identifier to a new app auto-links to existing packages.
type: reference
---

S51: Wired App Store IAPs into the existing default offering. Spent time hunting for an "Attach product" button at the package level — it doesn't exist. The linking happens elsewhere.

**RC project hierarchy:**
- **Project** ("Speech to Video") — top-level container.
- **Apps** under Project — one per store. We have two: "Test Store" (RC's sandbox) + "Speech to Video (App Store)" (real Apple). Each App has its own SDK key (`test_*` vs `appl_*`).
- **Products** are scoped to one App. Same SKU `pro_pack_50` exists as TWO products — one Test Store entry, one App Store entry — both with identifier `pro_pack_50`.
- **Offerings** are project-scoped. Each Offering contains Packages. A **Package can attach one product per app** ("You can only select one product per app" — RC's wording).

**The auto-linking behavior that confused S51:** when you create a new product on a new App with an identifier that matches an existing package, RC auto-attaches it to that package. So creating App Store `pro_pack_50` after already having Test Store `pro_pack_50` in a package = no manual attach step needed.

**Where to verify/edit attachments:** Offerings tab → open the offering → click **Edit** in the header. Each package row shows a **Products** section listing one row per app in the Project, each with a dropdown of that app's products. Empty dropdown = package won't resolve for that app's SDK key. Save commits the attachments.

**Single-offering = implicit Current.** With only one offering, `Purchases.getOfferings().current` returns it without any explicit toggle. Toggle becomes relevant when a second offering exists.

**Receipt validation prerequisite:** RC needs an App Store Connect **In-App Purchase Key** (.p8 + Key ID + Issuer ID) uploaded under Project Settings → Apps → iOS App Store → "In-App Purchase Key configuration" before it can verify App Store receipts. Generate this in ASC under Users and Access → Integrations → App Store Connect API → **In-App Purchase** section (NOT the standard ASC API key).

**Post-create propagation:** RC products linked to App Store show "Could not check" status until Apple ingests the IAPs (hours, sometimes a day). Auto-flips to "Active" once verified. Not actionable; just wait.
