# QA — Paywall & Credits Edge Cases

Manual cases to run alongside the Session 45 golden-path verification script in NOW.md.

## 1. Offline when paywall opens

**Setup:** Put the simulator into Airplane Mode (Settings → Airplane Mode ON), then trigger the paywall (tap Buy Credits in Settings, or exhaust credits and tap Generate).

**Expected:**
- `Purchases.getOfferings()` rejects → `loadError` renders as a red banner inside the paywall.
- The pack rows show `—` for price and are disabled (opacity 0.5).
- CTA button reads "Loading…" and is disabled.
- Restore button is present but `restoreAndGrant` will also fail — surfaced as `purchaseError`.

**Fail signals:**
- Paywall renders without error banner and with empty/zero-priced rows.
- CTA enabled while offline.
- App crashes or hangs.

## 2. Grant exhausts all retries on 404

**Setup:** Hardest to simulate without server-side hooks. Options:
- Temporarily break the RC REST API key in backend `.env` (`REVENUECAT_REST_API_KEY=invalid`) so `/api/credits/grant` always returns 500 — NOT 404, so this test doesn't match. Skip.
- Point the mobile build at a backend that lags: mock the server locally to return 404 `purchase_not_found_yet` for all grant calls.
- Alternatively use a StoreKit sandbox purchase with RC's known ingestion lag and race the first grant attempt before RC catches up. Unreliable timing.

**Preferred approach:** Run a local backend patched to return `raise HTTPException(404, "purchase_not_found_yet")` unconditionally in `api/credits.py:grant_credits`. Point mobile at it via `API_BASE`.

**Expected:**
- Purchase completes in the Test Store sheet (user is charged in sandbox).
- Mobile retries `/api/credits/grant` at 0s / 1s / 2s / 4s (4 attempts, ~7s total).
- On final failure, Paywall stays open, `refreshCredits` runs, and inline text reads:
  "Credits delayed — tap Restore if they aren't applied."
- Tapping Restore afterwards re-invokes `grantCreditsForTransaction` via `restoreAndGrant`; once the server is patched back to normal, Restore should succeed and credits appear.

**Fail signals:**
- Paywall closes without credits being granted and without the delayed-credits message (user loses money silently).
- Retries fire more or fewer than 4 times, or at wrong intervals.
- `creditBalance` never refreshes on grant failure.
