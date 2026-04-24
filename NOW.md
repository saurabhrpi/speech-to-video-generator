# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 50 — 2026-04-23 — main (closed)
**Status:** Tier 1 paywall edge cases all 6/6 PASS. Four S50 bug fixes shipped + pushed (commit `69a1a41`). Submission-path R/Y/G traffic-light added to `LAUNCH_CHECKLIST.md`. Ready to pick up Red-item #1 (Account deletion UI) next session.

## What happened this session

- **Cases 2 + 6 PASS.** Completed S49's Tier 1 matrix. Cases 2 + 6 observations + bug-fix notes recorded in `QA/paywall_credits_edge_cases.md` (local-only).
- **Credit-bypass TOCTOU discovered + client-side mitigation shipped.** User hit the bypass during Case 2: rapid Generate taps against 5-credit anon balance started N concurrent jobs (all passed submit-time check), first completion debited balance, subsequent completions logged `"shortfall at completion"` and served free videos. Ranked fix options A/B/C. MiniMax docs research (delegated to agent) confirmed **no upstream backstop** — no sub-accounts, no per-user quotas, no programmatic keys. Shipped: client-side projected-balance check in `auth-store.canAfford` (`creditBalance − sum(in-flight costAtSubmit) >= cost`), Generate button disabled ONLY when in-flight is the blocker (truly-empty case falls through to open paywall). Server-side atomic guard is now ToDo #1 (must land before TestFlight wider release).
- **Stale-balance-on-signout fix.** `auth-store.initialize` now resets `creditBalance` + `costTable` whenever the UID changes, so a previous user's balance can't gate the new user's check. Found when anon→Apple→SignOut left Settings showing the Apple-linked user's 200-credit balance despite being anon again.
- **Button disabled state finally visible.** `Button.tsx` `animatedStyle` was always writing `opacity: 1`, silently overriding the `disabled && 'opacity-50'` className. Baked the disabled fade into `animatedStyle`.
- **Paywall refactored off RN `<Modal>` → root-level `Animated.View` overlay.** Recurring X-stuck-after-Apple-Sign-In-cancel bug (repro 3/3 before fix). `transparent={true}` on Modal did NOT help — iOS still treats it as a separate presentation. Overlay approach (same View tree, no separate iOS window) fixed both the new bug AND the prior Settings→Paywall stacking issue. Slide animation via reanimated `withTiming(280ms)`. Mounted in `_layout.tsx` after `<Stack>`.
- **Memory consolidated.** `reference_ios_modal_on_modal.md` rewritten to cover both stacking scenarios (Scenario A: expo-router modal route → RN Modal; Scenario B: native iOS sheet → RN Modal) and the durable overlay pattern with reference code. MEMORY.md index updated. One new reference memory for MiniMax's upstream-quota gaps.
- **ToDo cleanup + reordering.** Promoted server-side TOCTOU credit gate to #1 (revenue leak, must land before TestFlight wider release). Removed resolved items (lazy anon sign-in S41, paywall X-stuck S50). Added two new items: Generate-button silent-disable poor UX (#20), story-continuation prompt nudge (#21). Updated cross-references after renumber.
- **Launch checklist updated with R/Y/G submission priority.** Account deletion + ASC IAPs + metadata + UI polish + reviewer demo + product vision + TestFlight smoke → Red (block review). Server TOCTOU + grant-reliability + backend audit + SSE-kill testing → Yellow (post-submit hardening). Post-launch monitoring + smaller UX → Green. Removed duplicated top-level items that R/Y/G now covers.
- **Commit + push landed** (`69a1a41`). `NOW.md` and `QA/paywall_credits_edge_cases.md` intentionally excluded — NOW handled at /close (now), QA doc is local-only.

## Next step — Session 51 (on resume)

**1. Pick a Red item from `LAUNCH_CHECKLIST.md`'s Submission Priority section.** Recommended starting point: **Red #1 — Account deletion UI** (Guideline 5.1.1(v), guaranteed rejection without it). Scope:
- Mobile: add "Delete Account" row in Settings below Purchases, gated behind a confirm modal (`ConfirmModal` already exists). On confirm, call new backend endpoint + Firebase `user.delete()` + local state wipe.
- Backend: new `DELETE /api/account` endpoint — deletes Firebase user (via `firebase_admin.auth.delete_user`), Firestore `credits/{uid}` doc, and per-uid clip namespace (`clip_store.delete_namespace(uid)`). Idempotent — missing records are a no-op, not an error.
- Test: anon delete (no Apple linkage, just wipes anon state), signed-in delete (wipes Apple-linked state, kills session so app drops to anon on next launch).

**2. Or Red #2 — ASC IAPs + RC product swap** if you want to do the ASC dashboard work in parallel (Apple propagation takes hours, good to kick off early). Dashboard-only, no code change needed since `__DEV__` key switch already routes prod to App Store.

**3. Or Red #4 — UI polish pass** if you want to tackle the highest-risk item head-on. No dependencies, big reviewer-perception lever.

## Open questions (carryover + new)

- **(S48 follow-up B, still open) UX hole: home button shows cost not balance.** `mobile/app/(tabs)/index.tsx` Generate button shows `Generate Video · N credits` (cost per next gen), not the user's current balance. Users can't see how many gens they have left from the home tab — they have to navigate to Settings. Decision needed on placement before implementation: (a) chip above the Generate button, (b) subtitle under the screen header ("Speech to Video"), (c) badge on the gear icon. Holding for design taste; not blocking submit.
- **S2V Product Vision** still blank in CLAUDE.md (`NEEDS USER INPUT`). Affects paywall copy + reviewer perception (feeds 4.3a risk). Needs user input before Red items #4 and #6 can land cleanly.
- **Real Terms/Privacy URLs** — `mobile/lib/constants.ts` still has placeholders. Blocker for Red #3 (metadata).
- **Kling COGS tuning** — `CREDIT_COSTS` in `api/server.py` uses ~1.5 credits/sec placeholder. Tune when real Kling billing numbers land. `mobile/lib/constants.ts:FALLBACK_COSTS` must stay in sync.
- **Backend Apple precheck + clip-merge** — Yellow #10. Haven't verified `/api/auth/apple/precheck` + `/api/clips/merge` exist in `server.py`. If missing, clip-orphan risk on anon→Apple collision.
- **(S48 carryover, still open) Anon→Apple credit merge** — old anon UID's `credits/{uid}` doc orphans at link-time; new linked UID gets `starter_granted: false` and a fresh row. No harm in current bundled flow (sign-in always precedes purchase). If we ever allow purchase pre-sign-in, this needs cross-UID merge from Task #7.
- **(S48-era carryover, now superseded by ToDo #1)** Credits consume on job completion, not submission. Was filed as "Acceptable MVP" in S49 — server restart mid-job loses the job but not the credit. **S50 reversal:** the same consume-at-completion strategy is what enables the concurrent-submit bypass (TOCTOU). No longer acceptable — tracked as the top-priority server fix in ToDo #1.
- **(S43-era carryover, still open)** RC `default` offering "Current" state — only one offering exists today so it's implicitly the current one. If `Purchases.getOfferings().current` returns `null` after a second offering is ever added, check the RC dashboard for an explicit "Current" toggle.
- **(S49 carryover)** iCloud on sim flaky on hang — if it recurs persistently, move anon-path QA to physical device via TestFlight.
- **(S50 observation)** The `router.back() + setTimeout(400)` workaround in `mobile/app/settings.tsx` (S49 Settings→Paywall fix) is now redundant since Paywall is no longer a Modal. Worth removing in the next PR that touches settings.tsx.
