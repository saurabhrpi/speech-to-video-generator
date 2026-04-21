# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 46 — 2026-04-20 — main
**Status:** Mobile credit-system refactor done, typecheck-clean, unrun on simulator.

## What happened this session
- Shipped the 6-file mobile refactor for LAUNCH_CHECKLIST Task #8 steps 4-8: `mobile/lib/constants.ts`, `mobile/store/auth-store.ts`, `mobile/store/gallery-store.ts`, `mobile/components/Paywall.tsx`, `mobile/app/(tabs)/index.tsx`, `mobile/app/settings.tsx`.
- Factored `grantCreditsForTransaction` + `restoreAndGrant` into `mobile/lib/purchases.ts` so Paywall and Settings share the grant + retry + restore helpers.
- Typechecked clean (`npx tsc --noEmit`) across all touched files. Only error is a pre-existing Reanimated typing quirk in `Button.tsx`.
- Code-reviewed the diff; 3 polish follow-ups captured below. No blockers.
- Added `QA/paywall_credits_edge_cases.md` covering offline-at-paywall-open and grant-404-exhaustion.

## Next step — Session 47

**1. Verification after refactor (before shipping):**
- Fresh install (`xcrun simctl erase booted` — per `memory/reference_simulator_keychain_persists.md`) → anon user → `/api/auth/session` returns `credit_balance: 5` + `cost_table` → UI shows 5.
- Hailuo 6s → button reads "Generate Video · 5 credits" → tap → generation completes → balance drops to 0.
- Retry → `!canAfford` → paywall opens, shows 3 packs.
- Buy `pro_pack_50` → Apple Sign In sheet (bundled) → IAP sandbox sheet → `Purchases.purchasePackage` resolves → `/api/credits/grant` → balance → 50 → paywall closes.
- Settings shows updated balance; Restore works (tear off and re-install, then Restore → credits reappear).
- Cross-check: RC dashboard Customers tab shows the purchase against the Firebase UID; Firestore `credits/{uid}` doc reflects balance.

**2. Edge cases** — run the two cases in `QA/paywall_credits_edge_cases.md` after the golden path passes.

**3. Apply the code-review follow-ups** (see below).

## Follow-ups from code review (Session 46)

- **`restoreAndGrant` should report granted count.** Currently swallows per-tx grant failures silently (`mobile/lib/purchases.ts:84`); if all grants fail, Paywall still calls `closePaywall()` with unchanged balance. Return `{grantedCount, attempted}` and surface a warning in the Paywall/Settings UIs when count is 0.
- **Swap `pkg.identifier` → `pkg.product.identifier` in grant call.** In `mobile/components/Paywall.tsx:122` the `product_id` sent to `/api/credits/grant` is the RC package identifier; it works today only because Session 45 set them equal in the RC dashboard. Using `pkg.product.identifier` (the actual store product id) is semantically correct and survives any future ASC product-id rename.
- **Loading state for Settings credit row.** `mobile/app/settings.tsx:41` shows `Credits: —` both before the fetch lands and when the fetch fails. Use `…` (or an `ActivityIndicator`) while `creditBalance === null && loading`, reserve `—` for the post-fetch null case.

## Open questions

- **Kling COGS still TBD** — `CREDIT_COSTS` in `api/server.py` uses the ~1.5 credits/sec placeholder (Kling 3s=5, 10s=15, 15s=23). Tune when real numbers land. `mobile/lib/constants.ts:FALLBACK_COSTS` must stay in sync.
- **S2V Product Vision** (mission, target user, quality bar) still blank in CLAUDE.md (`NEEDS USER INPUT`). Paywall copy defaults to a generic "Buy Credits" until this is pinned down.
- **Terms/Privacy URLs still placeholder** (`mobile/lib/constants.ts`).
- **Anon→Apple collision path**: credit merge across UIDs not handled (parallel to clip-merge in LAUNCH_CHECKLIST Task #7). Defer until both are tackled together.
- **Credits consume on job completion, not submission** — if the server restarts mid-job the job is lost but the credit wasn't spent. Acceptable MVP.
- **RC `default` offering "Current" state** — only one offering exists so it's implicit. If `Purchases.getOfferings().current` returns null on first paywall test, check the dashboard for an explicit Current toggle that RC may add once a second offering exists.
