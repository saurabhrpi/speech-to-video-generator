"""Read V2 generation telemetry back from Firestore (collection `gen_events`).

This is the replacement for scraping the Replit console: every runtime
template gen writes a durable event here (src/speech_to_video/utils/gen_telemetry.py),
so reliability stats and failure post-mortems are one query away with the same
firebase-admin credentials the backend uses.

Reports against the SLA the product targets: success rate, the fraction that
completed within 5 min and within 6 min, latency percentiles, and a table of
recent failures (Kling task_id + timeout-vs-reject label + error).

Usage:
    python scripts/gen_telemetry_report.py                       # last 200 events
    python scripts/gen_telemetry_report.py --limit 1000
    python scripts/gen_telemetry_report.py --since-hours 24
    python scripts/gen_telemetry_report.py --template viral-dances-git-up
    python scripts/gen_telemetry_report.py --failures-only --limit 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import gen_telemetry  # noqa: E402

# SLA thresholds (ms). Product target: 99.99% of prod gens succeed within 5 min,
# 6 min at the absolute outer edge — a breach of either is itself a failure.
SLA_GOOD_MS = 5 * 60 * 1000
SLA_MAX_MS = 6 * 60 * 1000


def _percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (pct / 100) * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def _fmt_ms(ms):
    if ms is None:
        return "—"
    return f"{ms / 1000:.0f}s" if ms < 60_000 else f"{ms / 60000:.1f}m"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=200, help="max events to scan (newest first)")
    ap.add_argument("--since-hours", type=float, default=None, help="only events in the last N hours")
    ap.add_argument("--template", default=None, help="filter to one template_id")
    ap.add_argument("--outcome", default=None, help="filter to one outcome")
    ap.add_argument("--failures-only", action="store_true", help="hide successes in the failure table")
    args = ap.parse_args()

    from firebase_admin import firestore as fb_firestore

    db = gen_telemetry._db()
    q = (
        db.collection("gen_events")
        .order_by("created_at", direction=fb_firestore.Query.DESCENDING)
        .limit(args.limit)
    )
    rows = [d.to_dict() for d in q.stream()]

    # Python-side filters (keeps us index-free at launch volume).
    if args.since_hours is not None:
        import datetime as _dt
        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=args.since_hours)
        rows = [r for r in rows if (r.get("created_at") and r["created_at"] >= cutoff)]
    if args.template:
        rows = [r for r in rows if r.get("template_id") == args.template]
    if args.outcome:
        rows = [r for r in rows if r.get("outcome") == args.outcome]

    n = len(rows)
    if n == 0:
        print("No telemetry events match the filters.")
        return 0

    # --- Outcome breakdown ---
    by_outcome = {}
    for r in rows:
        by_outcome[r.get("outcome", "?")] = by_outcome.get(r.get("outcome", "?"), 0) + 1
    successes = [r for r in rows if r.get("outcome") == "success"]
    n_success = len(successes)

    print(f"\n=== gen telemetry — {n} events scanned ===")
    print(f"success rate:  {n_success}/{n}  ({100 * n_success / n:.2f}%)")
    print("outcomes:      " + ", ".join(f"{k}={v}" for k, v in sorted(by_outcome.items(), key=lambda kv: -kv[1])))

    # --- SLA: of the SUCCESSES, how many landed within 5 / 6 min ---
    succ_total = sorted(r["total_ms"] for r in successes if r.get("total_ms") is not None)
    if succ_total:
        within5 = sum(1 for v in succ_total if v <= SLA_GOOD_MS)
        within6 = sum(1 for v in succ_total if v <= SLA_MAX_MS)
        print(f"\n--- SLA (successful gens, n={len(succ_total)}) ---")
        print(f"within 5 min:  {within5}/{len(succ_total)}  ({100 * within5 / len(succ_total):.2f}%)")
        print(f"within 6 min:  {within6}/{len(succ_total)}  ({100 * within6 / len(succ_total):.2f}%)")
        print("total latency: " + "  ".join(
            f"p{p}={_fmt_ms(_percentile(succ_total, p))}" for p in (50, 90, 95, 99)
        ))
        kling = sorted(r["kling_ms"] for r in successes if r.get("kling_ms") is not None)
        if kling:
            print("kling latency: " + "  ".join(
                f"p{p}={_fmt_ms(_percentile(kling, p))}" for p in (50, 90, 95, 99)
            ))

    # --- Failure table ---
    fails = [r for r in rows if r.get("outcome") != "success"]
    if fails and (args.failures_only or True):
        print(f"\n--- recent failures (n={len(fails)}) ---")
        for r in fails[:30]:
            ts = r.get("created_at")
            ts_s = ts.strftime("%m-%d %H:%M") if ts else "?"
            err = (r.get("error") or "")[:80].replace("\n", " ")
            print(
                f"  {ts_s}  {r.get('outcome'):14s}  "
                f"stage={r.get('failure_stage') or '—'}  "
                f"last={r.get('last_task_status') or '—'}  "
                f"kling={_fmt_ms(r.get('kling_ms'))}  "
                f"task={r.get('kling_task_id') or '—'}  "
                f"tmpl={r.get('template_id') or '—'}\n"
                f"      err: {err}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
