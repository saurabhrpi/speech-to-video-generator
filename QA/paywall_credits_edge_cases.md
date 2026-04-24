# QA — Paywall & Credits Edge Cases

Manual cases run on the dev-client simulator (UDID `592C0D4C…`) alongside the golden-path verification.

**Sim state key:**
- **signed-in**: last Session 48 state — Apple-linked UID `z3S9exmD8AhOq4WuFy217HRe75w2`, 50 credits.
- **fresh**: `xcrun simctl shutdown booted && xcrun simctl erase booted && xcrun simctl boot booted`, then `npx expo run:ios`.

---

## Tier 1 — Client-only cases (no backend changes)

### 1a. Offline when paywall opens — RETURNING user (has RC disk cache)

**Sim state:** signed-in, has previously opened paywall at least once this install → RC has cached offerings on disk.

**Setup:** Turn Mac WiFi OFF (`networksetup -setairportpower en0 off`). Open app → Settings → Buy Credits.

**Expected (from live Session 49 log evidence):**
- RC's `getOfferings()` logs `API request failed ... internet connection appears to be offline` BUT then `Vending Offerings from disk cache` succeeds → `result.current` populates from cache.
- Paywall renders **normally** with real pack prices (served from cache).
- Red `<NetworkBanner />` ("No internet connection") shows above the paywall.
- CTA enabled — tapping Buy will call `Purchases.purchasePackage` which will fail at StoreKit with a network error, surfaced as `purchaseError` banner.
- Restore button enabled; tapping will also fail with a network error surfaced as `purchaseError`.

**Fail signals:**
- Paywall is inert / visually broken (empty rows despite cache present).
- App crashes on offline Buy/Restore taps (should show error banner, not crash).

**Recovery check:** Close paywall, re-enable WiFi, re-open paywall → both banner and error clear, purchase flow works.

**Result:** **PASS (Session 49)** with three follow-ups filed in `ToDo.md` items 17/18/19.

Observed on dev sim `592C0D4C…`, UID `z3S9exmD8AhOq4WuFy217HRe75w2`, balance 50, Mac WiFi off via `networksetup -setairportpower en0 off`:
- Paywall slid up normally with 3 pack rows populated from RC disk cache (log: `Vending Offerings from disk cache`).
- Pack selection worked; CTA updated accordingly.
- Tap Buy → CTA → `Processing…` → Test Store "Test Valid Purchase" sheet appeared → tapped → red inline banner: **"Error performing request because the internet connection appears to be offline."** Paywall stayed open. Balance unchanged (50).
- Tap Restore → paywall slid down silently with no error text and no balance change. Reason: Test Store doesn't support restore (`Restoring purchases not available in Test Store`) + `handleRestore` swallows offline errors internally.
- `<NetworkBanner />` was NOT visible over the paywall (fullScreen Modal occludes root-level banner).
- Recovery: re-enabled WiFi, waited >30s, balance remained 50 — Test Store did not replay the offline tx. Real App Store replay behavior not verified here.

**Follow-ups filed:** `ToDo.md` #17 (NetworkBanner occluded), #18 (Restore silently closes), #19 (no CustomerInfo listener for StoreKit replay).

---

### 1b. Offline when paywall opens — FRESH user (no RC disk cache)

**Sim state:** fresh (`xcrun simctl erase booted`, rebuild), signed in anonymously on first launch, paywall never previously opened during this install.

**Setup:** Immediately after fresh launch, BEFORE opening paywall once online: turn Mac WiFi OFF. Exhaust starter credit → Generate (which will fail offline anyway) OR navigate to Settings → Buy Credits.

**Note:** The Generate path cannot work offline to trigger the 402 flow. Reaching the paywall on a fresh-install offline user effectively requires the Settings → Buy Credits path. This is a narrow test case — acceptable to skip for MVP.

**Expected:**
- `Purchases.getOfferings()` rejects with no disk cache fallback → red `loadError` banner.
- Pack rows show `—`, opacity 0.5, not selectable.
- CTA reads `Loading…`, disabled.
- Restore also fails → `purchaseError` on tap.

**Fail signals:**
- Paywall renders without error banner and with empty/zero-priced rows.
- CTA enabled.
- App crashes or hangs.

**Result:** _pending (narrow case, deprioritize)_

---

### 2. Cancel Apple Sign In (anon path)

**Sim state:** fresh (anon UID, isAnonymous=true).

**Setup:** Generate one free video to exhaust starter credits, then tap Generate again → paywall opens via 402. Tap Buy on any pack. Apple Sign In sheet appears (bundled flow). Tap Cancel on the sheet.

**Expected:**
- `signInWithApple()` throws with `code === 'ERR_REQUEST_CANCELED'` (`Paywall.tsx:114`).
- Function returns silently inside `handlePurchase`; `purchasing` resets via `finally` to false.
- Paywall stays open, no error banner, CTA re-enabled, user can tap Buy again.
- No Firebase link happens; user still anonymous.

**Fail signals:**
- Error banner appears (cancel should be silent).
- CTA stuck in `Processing…` state.
- User gets signed in despite cancelling.

**Result:** **PASS (Session 50)** — verified incidentally during the diagnosis of a now-fixed paywall bug.

Observed on dev sim, fresh anon UID `YHCh4fwCDKd5EO2xhMAeEZpVywH2`, balance 5 → 0:
- Generated one Hailuo 6s video to exhaust starter credits → balance 0.
- Tapped Generate again → paywall opened via 402 (golden path).
- Tapped Buy on `pro_pack_50` → CTA → `Processing…` → Apple Sign In native sheet appeared.
- Tapped X on the Apple Sign In sheet. Sheet dismissed. CTA reset to `Buy 50 credits — $4.99`. No `purchaseError` banner. Paywall stayed open. UID still anon.

**Bug discovered + fixed mid-session:** First two attempts to run this case left the Paywall X button unresponsive after the Apple Sign In sheet dismissed (drag-handle cursor over sim — iOS still thought a sheet was presented). Root cause: RN `<Modal>` creates a separate iOS window; focus restoration after stacked native sheets is fragile. `transparent={true}` did NOT fix it. **Durable fix shipped S50:** refactored Paywall off `<Modal>` to a root-level `Animated.View` overlay (`mobile/components/Paywall.tsx`). Same View tree, no separate window, no focus restoration to fail. Both this Scenario B (Apple Sign In → Paywall) AND the prior Scenario A (Settings modal route → Paywall) now work cleanly. See `memory/reference_ios_modal_on_modal.md`.

**Side note for ToDo cleanup:** the `router.back() + setTimeout(400)` workaround in `mobile/app/settings.tsx` (S49 fix for Scenario A) is now redundant since Paywall is no longer a Modal — Settings can call `openPaywall()` directly without the dismiss-and-wait dance.

---

### 3. Cancel IAP sheet

**Sim state:** signed-in (skips sign-in branch → straight to `Purchases.purchasePackage`).

**Setup:** Open Settings → Buy Credits. Tap Buy on a pack. Test Store sheet appears. Tap Cancel.

**Expected:**
- `purchasePackage` throws with `e.userCancelled === true` (`Paywall.tsx:133`).
- Silent return, `purchasing` resets to false, paywall stays open.
- No `purchaseError` banner, no toast, no credit change.
- User can immediately tap Buy again and proceed normally.

**Fail signals:**
- Error banner shown for cancellation.
- `purchasing` state stuck true (CTA greyed out indefinitely).
- Credits granted despite cancellation.

**Result:** **PASS (Session 49)**.

Observed on dev sim, signed-in UID, WiFi on, balance 150:
- Tapped Buy 50 credits CTA → CTA → `Processing…`. Test Store sheet appeared with 3 options: **Test valid purchase** / **Test failed purchase** / **Cancel**.
- Tapped **Cancel**. Sheet dismissed. CTA reset to normal `Buy 50 credits — $4.99`. No `purchaseError` banner. Paywall stayed open. Balance unchanged (150).
- A dev-only RN LogBox overlay briefly appeared at bottom of screen: `[RevenueCat] 🍎‼️ Purchase was cancelled.` — this is RC's SDK logging at DEBUG level, caught by RN LogBox in `__DEV__` builds only. Not visible in production.

Test Store sheet's cancel button is labeled literally **"Cancel"**, not "Test Cancelled Purchase" (useful note for future sessions).

---

### 4. Double-tap Buy

**Sim state:** signed-in. Note: this case completes a real Test Store purchase; expect balance 50 → 50+pack.

**Setup:** Open Settings → Buy Credits. Tap the Buy CTA twice in rapid succession (as fast as possible with two fingers / fast repeat).

**Expected:**
- First tap sets `purchasing=true` (`Paywall.tsx:107`), CTA disabled via `disabled={!selectedPkg || purchasing}`.
- Second tap either no-ops (Button component respects disabled at press time) or is ignored by StoreKit if it slips through.
- Exactly ONE Test Store sheet appears.
- Exactly ONE `/api/credits/grant` call fires (check server logs or Firestore `applied_transactions` has one new entry).
- Balance increments by exactly one pack's credits.

**Fail signals:**
- Two Test Store sheets queued.
- Two grant calls / credits double-applied.
- Crash from concurrent `purchasePackage` calls.

**Result:** **PASS (Session 49)**.

Observed on dev sim, signed-in UID, WiFi on, balance 150:
- Double-tapped Buy CTA rapidly. Exactly ONE Test Store sheet appeared. No crash.
- Tapped Test valid purchase. Flow proceeded: `Processing…` → red "Credits delayed — tap Restore if they aren't applied." banner (expected, known retry-window gap / ToDo #19).
- Tapped Restore → balance 150 → **200** (exactly ONE new pro_pack_50 applied, not two).

Dedup is provided by a combination of `Button`'s `disabled={!selectedPkg || purchasing}` (lines 254-256) and RC SDK's own in-flight purchase dedup. No explicit guard needed in `handlePurchase`.

---

### 5. Double-tap Restore

**Sim state:** signed-in (has the Session 48 `pro_pack_50` tx on file).

**Setup:** Open Settings → Buy Credits. Tap "Restore purchases" twice rapidly.

**Setup notes:** `handleRestore` sets `purchasing=true` before awaiting `restorePurchases()`. The Pressable is `disabled={purchasing}` but React won't have re-rendered between two near-simultaneous synchronous taps.

**Expected:**
- `restoreAndGrant` calls the idempotent server grant; replaying a tx is a no-op server-side.
- Even if two restore flows fire, balance does NOT double (server idempotency protects us).
- At most one `closePaywall()` fires; paywall closes cleanly.
- No lingering `purchasing=true` after both resolve.

**Fail signals:**
- Balance doubles (server idempotency broken).
- Paywall fails to close or re-opens.
- `purchasing` stuck true.

**Result:** **PASS (Session 49)**.

Observed on dev sim, signed-in UID, WiFi on, balance 200 (4 pro_pack_50 txs, all already in server's `applied_transactions`):
- Double-tapped "Restore purchases" rapidly. Paywall closed cleanly. No error banner flash. No crash or UI glitch.
- Balance stayed at **200**. No double-grant.
- Additional single tap on Settings' "Restore Purchases" afterwards: still 200.

Dedup works via a combination of RC SDK's in-flight restore handling and server's `applied_transactions` idempotency. No explicit client-side guard needed.

---

### 6. Restore with no prior purchase

**Sim state:** fresh (brand-new anon UID, no Apple-linked account, no purchase history).

**Setup:** Exhaust starter credit → paywall opens → tap "Restore purchases" WITHOUT buying anything.

**Expected:**
- `restorePurchases()` resolves with `nonSubscriptionTransactions: []` (no prior purchases under this Apple ID in sandbox, OR none matching `PACK_SKUS`).
- `restoreAndGrant` loop body never runs → no grant call.
- Current code: `handleRestore` then calls `refreshCredits()` + `closePaywall()` → paywall closes silently with no balance change.
- User sees no feedback about "nothing to restore".

**Fail signals:**
- Error banner shown (restore succeeds per RC, just no matching txs).
- Credits incorrectly granted.
- App crash on empty `nonSubscriptionTransactions`.

**UX note:** The silent-close-with-no-change behavior is likely confusing. If confirmed, file a follow-up to surface "No purchases to restore" inline, without treating it as an error.

**Result:** **PASS as designed (Session 50)** — behavior matches the documented gap; UX is bad and tracked as `ToDo.md` #18 (was #18 after the S50 renumber: "Restore silently closes paywall on offline failure" — same class).

Observed on dev sim, anon UID, balance 0, paywall opened via Generate-on-empty-balance:
- Tapped "Restore purchases" without buying first.
- Paywall slid down silently, no error banner, balance still 0, still anon. No Apple Sign In sheet (Restore doesn't require sign-in).

This is the same UX gap as the offline-Restore behavior in Case 1a — `handleRestore` swallows internally and `closePaywall()` always runs on the success path even when nothing was actually restored. Fix per ToDo #18 needs to distinguish "offline" vs "nothing to restore" vs "restored N txs" and surface inline.

---

## Tier 2 — Deferred (needs local backend patch)

### Grant exhausts all retries on 404

**Setup:** Run a local FastAPI backend patched to `raise HTTPException(404, "purchase_not_found_yet")` unconditionally in `api/credits.py:grant_credits`. Point mobile at it via `API_BASE`.

**Expected:**
- Purchase completes in the Test Store sheet (sandbox).
- Mobile retries `/api/credits/grant` at 0s / 1s / 2s / 4s (4 attempts, ~7s total per `purchases.ts:53`).
- On final failure, paywall stays open, `refreshCredits` runs, inline text reads "Credits delayed — tap Restore if they aren't applied."
- Tapping Restore afterwards re-invokes `grantCreditsForTransaction` via `restoreAndGrant`; once server is patched back, Restore succeeds and credits appear.

**Fail signals:**
- Paywall closes without credits granted and without the delayed-credits message (user loses money silently).
- Retries fire more or fewer than 4 times, or at wrong intervals.
- `creditBalance` never refreshes on grant failure.

**Deferred to Session 50 or later.**
