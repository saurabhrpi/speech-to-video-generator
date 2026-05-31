"""Coin redenomination migration (S87): multiply every user's credit ledger by 10.

WHY: we are moving from 10 coins = $1 to 100 coins = $1. Pack grants, anon
starter, and template prices all switch to the new denomination in code/Firestore.
Existing users' BALANCES must scale x10 too, or their real-dollar value silently
drops 10x. This migrates the `credits/{uid}` ledger docs.

INVARIANT: balance = granted - used. All three are multiplied by `factor` so the
invariant holds. `applied_transactions` (RC idempotency ids) and `starter_granted`
are untouched.

IDEMPOTENT: each migrated doc gets a marker field (`redenom_v2_applied: true`).
Re-running skips already-migrated docs, so it can never x10 twice. Each doc is
updated inside a Firestore transaction.

SAFETY: dry-run by default — reads and projects, writes NOTHING. Pass --apply to
write. Real money: review the dry-run totals before applying.

⚠️ DEPLOY COUPLING: run this together with (not before/after a long gap) the code
redenomination (pack grants x10, anon starter x10) AND the duration-pricing writes.
If balances are x10 but template prices are still old (or vice versa), users have
the wrong spending power for the window in between.

Usage:
  .venv/bin/python scripts/migrate_coins_redenomination.py              # dry-run
  .venv/bin/python scripts/migrate_coins_redenomination.py --apply      # execute
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(str(ROOT / ".env"), override=True)

from src.speech_to_video.utils import credit_store  # noqa: E402

MARKER = "redenom_v2_applied"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Write the x10 (default: dry-run).")
    ap.add_argument("--factor", type=int, default=10, help="Multiplier (default 10).")
    ap.add_argument("--show-zero", action="store_true", help="Also list zero-balance ledgers.")
    args = ap.parse_args()

    from firebase_admin import firestore as fb_firestore
    db = credit_store._db()
    snaps = list(db.collection("credits").stream())

    print(f"\nMODE: {'APPLY (will write)' if args.apply else 'DRY-RUN (no writes)'} | factor x{args.factor}")
    print(f"ledgers found: {len(snaps)}\n")

    hdr = f"{'uid (trunc)':26} {'bal':>8} {'->':>3} {'new_bal':>8} {'granted':>8} {'used':>7} {'status':>10}"
    print(hdr); print("-" * len(hdr))

    tot_old = tot_new = 0
    n_migrate = n_skip = n_zero = 0
    to_write = []
    for s in snaps:
        d = s.to_dict() or {}
        bal = int(d.get("balance", 0)); gr = int(d.get("granted", 0)); us = int(d.get("used", 0))
        already = bool(d.get(MARKER))
        if already:
            n_skip += 1
            status = "skip(done)"
            new_bal = bal
        else:
            new_bal = bal * args.factor
            to_write.append(s.id)
            n_migrate += 1
            status = "MIGRATE"
        tot_old += bal
        tot_new += new_bal if not already else bal
        if bal == 0 and not args.show_zero:
            if bal == 0:
                n_zero += 1
            continue
        print(f"{s.id[:26]:26} {bal:>8} {'->':>3} {new_bal:>8} {gr:>8} {us:>7} {status:>10}")

    print("-" * len(hdr))
    print(f"to migrate: {n_migrate} | already done: {n_skip} | zero-balance hidden: {n_zero}"
          f"{' (shown)' if args.show_zero else ''}")
    print(f"total coins  before: {tot_old}  ->  after: {tot_new}")

    if args.apply:
        if not to_write:
            print("\nnothing to migrate (all done).")
            return 0
        print(f"\nApplying x{args.factor} to {len(to_write)} ledgers...")
        ok = 0
        for uid in to_write:
            ref = db.collection("credits").document(uid)
            tx = db.transaction()

            @fb_firestore.transactional
            def _run(t, ref=ref):
                snap = ref.get(transaction=t)
                if not snap.exists:
                    return False
                dd = snap.to_dict() or {}
                if dd.get(MARKER):
                    return False  # racing re-run guard
                t.update(ref, {
                    "balance": int(dd.get("balance", 0)) * args.factor,
                    "granted": int(dd.get("granted", 0)) * args.factor,
                    "used": int(dd.get("used", 0)) * args.factor,
                    MARKER: True,
                    "updated_at": fb_firestore.SERVER_TIMESTAMP,
                })
                return True

            if _run(tx):
                ok += 1
        print(f"migrated {ok}/{len(to_write)} ledgers.")
    else:
        print("\nDRY-RUN — nothing written. Re-run with --apply to execute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
