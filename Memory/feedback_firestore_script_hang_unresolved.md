---
name: feedback_firestore_script_hang_unresolved
description: OPEN PROBLEM — firebase-admin Firestore scripts hang forever from the local/Replit env, not yet root-caused or fixed; this memory tracks the investigation toward a real solution
metadata:
  type: feedback
---

> **🔴 OPEN PROBLEM — NOT SOLVED (as of S87).** This memory exists to drive toward
> a fix, not to document one. Running our firebase-admin Firestore scripts from the
> local environment hangs indefinitely. The root cause is **not yet confirmed** and
> there is **no verified fix**. Everything below is investigation state + candidate
> directions. Do not treat any item as "the solution."

## The problem
Ad-hoc Firestore scripts (`migrate_coins_redenomination.py`, ledger diagnostics)
**hang forever** mid-run — for both the agent and the user (user's run "went into an
unresponsive state"; had to Ctrl-C). It is intermittent: the SAME scripts worked
earlier in the same session (a dry-run printed 34 ledgers; flat-price wrote 45/45;
the first `--apply` returned) and then started hanging.

**Impact (real money):** the balance ×10 migration committed only SOME of the 34
ledgers before hanging → a partial migration. The user's ledger was a straggler
(showed 100 coins instead of ~1000). A partial run is indistinguishable from a
total failure without a working read-back. **The migration is still not verified
complete** — that confirmation is itself blocked by this hang.

## What we know / suspect (NOT fully root-caused)
- firebase-admin uses **gRPC, which has no default client deadline** — so a
  degraded channel blocks instead of raising. Plausible but unproven as THE cause.
- The hang is likely **before the Firestore RPC** — in the **google-auth OAuth2
  token fetch** (service-account JSON → access token over HTTP), or in channel
  setup. Evidence: adding `timeout=` to every Firestore call did NOT stop the hang
  (see below), and `Firestore timeout=` doesn't cover the token step.
- Unknown which of these it actually is: network/IPv6 black-hole, VPN/proxy, a
  Replit/local egress quirk, or DNS. **Pin this first** — don't code a fix blind.

## What was TRIED and did NOT work
- **Adding `timeout=` to every call + a `_preflight()` bounded read.** Handed it
  over believing it solved the hang; it **still hung past 10s**. Lesson: `timeout=`
  bounds the RPC only, not auth/channel setup — and I shouldn't have presented it as
  a fix before verifying it actually prevented the hang
  ([[feedback_save_memory_only_after_verification]]).

## Update — S88 (2026-05-31): network ruled out + reads work fast
Ran the step-1 probes below. **These findings sharpen the problem; it is NOT solved.**
- **Network branch RULED OUT.** `curl -m 8` to both `oauth2.googleapis.com/token`
  and `firestore.googleapis.com` returned **fast HTTP 404** (<0.2s total each; DNS
  ~20–34ms, connect ~33–47ms, TLS ~50–65ms). Per step-1's own decision tree, that
  means the issue is the **auth/channel layer — not network/VPN/DNS.**
- **A single READ did NOT hang.** A stage-marked, 60s-bounded fetch of the newest
  `gen_events` (`order_by(created_at desc).limit(6)`) completed with **`_db()`
  (firebase init + auth + channel) AND `.stream()` (the Firestore RPC) both inside
  the same 1-second window**, returning the row. So on S88 the token fetch, channel
  setup, and read RPC were all fast — the hang did not reproduce on a read.
- **Sharpened hypothesis:** the S87 hang happened during a **bulk WRITE loop** (the
  migration `.update()`-ing many ledgers in sequence). A clean read on S88 → the hang
  is plausibly **specific to bulk/batched writes, or intermittent** — NOT a blanket
  "every firebase-admin call hangs." (Reinforces the already-noted intermittency.)
- **Candidate fix direction (user, S88):** **batch the writes** — use a Firestore
  `WriteBatch` / `BulkWriter` instead of a per-doc `.update()` loop, so the migration
  issues far fewer separate RPC/channel round-trips (each a place a per-doc call can
  stall). Untested — validate against a *reproduced* hang first.
- **Still open:** one clean read does NOT prove the write path is fixed. Migration
  completeness remains **unverified** — deliberately NOT re-tested S88 (parked for
  later, to be done together with the batched-write attempt).

## How to actually solve it (investigation → fix)
1. **Root-cause first with hard-bounded probes** (each can't hang): ✅ **step-1 probe
   DONE S88 — network ruled out (see Update above); investigation now at step 2.**
   - `curl -m 8 https://firestore.googleapis.com` → fast HTTP code = reachable
     (problem is auth/channel layer); hang/err = network/VPN/DNS.
   - `curl -m 8 https://oauth2.googleapis.com/token` reachability for the token host.
   - Try IPv4-only / no-VPN / a different network to isolate the egress path.
2. **Instrument WHERE it blocks:** run with gRPC/auth debug logging
   (`GRPC_VERBOSITY=DEBUG GRPC_TRACE=...`, google-auth logging) so the hanging call
   is identified, not guessed.
3. **Then pick the fix that matches the proven layer:**
   - If auth-token fetch: bound it (google-auth `Request(timeout=…)`), or pre-mint
     credentials, or pass a deadline through.
   - If channel/network: fix the egress (IPv4, DNS, VPN), or run the script
     **server-side** where the service account + Firestore are co-located (likely
     the most robust — removes the local egress variable entirely).
   - As a universal backstop for any CLI: a **wall-clock guard** (run the work in a
     subprocess/thread, force-abandon after N s) so it errors instead of hanging.
     *Untested hypothesis — validate it actually bounds the token step.*
4. **Verify the fix by reproducing the hang first, then confirming it's gone** —
   don't ship another "should work."

## Stopgap only (NOT a fix, does NOT scale)
Editing a doc directly in the **Firebase Console** bypasses the local gRPC/auth
path entirely — that's how the user unblocked their single ledger (S87). Feasible
only for **1–few docs**; useless for a bulk migration, and it leaves the root cause
unsolved. Reach for it only to unblock, never as the resolution.

## Mitigations already in the script (help a partial run, don't cure the hang)
`timeout=` on every call; per-ledger try/except isolation; marker-guard idempotency
(safe to re-run, only touches stragglers); `--uid <id>` single-doc path. These make
a partial/retry safe — they do **not** stop the hang.

Sibling: [[feedback_one_clean_verification_not_flailing]] — this hang is the
infra-root behind several S87 "hangs" I first misattributed to the output channel.
