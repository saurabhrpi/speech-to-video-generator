"""Flat per-template pricing (S87) — set every template's credit_cost to one value.

Replaces the per-template/duration pricing idea with a single flat price for all
videos (500 coins by default). Prints a COGS vs price vs margin table — COGS is
duration-derived (Kling bills ~$0.07/sec on CEIL(sec), + NBP + Replit), so even
at a flat price the margin still varies by clip length. See
memory/reference_v2_runtime_cogs.md.

DENOMINATION (S87): 100 coins = $1.00.

SAFETY: dry-run by default — prints the table, writes NOTHING. Pass --apply to
write. Use --template-id to do ONE first (memory/feedback_incremental_change_and_test.md).

Usage:
  .venv/bin/python scripts/set_flat_template_price.py                       # dry-run all
  .venv/bin/python scripts/set_flat_template_price.py --template-id viral-dances-speed --apply
  .venv/bin/python scripts/set_flat_template_price.py --apply               # write all
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(str(ROOT / ".env"), override=True)

from src.speech_to_video.utils import template_registry  # noqa: E402


def probe_duration_sec(url: str, timeout: int = 90):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        p = subprocess.run([ff, "-i", url], capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        return None
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="Write credit_cost (default: dry-run).")
    ap.add_argument("--template-id", default=None, help="Price only this template id.")
    ap.add_argument("--price", type=int, default=500, help="Flat coins per video (default 500).")
    ap.add_argument("--coins-per-dollar", type=float, default=100.0)
    ap.add_argument("--kling-usd-per-sec", type=float, default=0.07)
    ap.add_argument("--nbp-usd", type=float, default=0.20)
    ap.add_argument("--replit-usd", type=float, default=0.25)
    ap.add_argument("--apple-cut", type=float, default=0.15)
    ap.add_argument("--include-drafts", action="store_true")
    ap.add_argument("--no-probe", action="store_true", help="Skip duration probe (no margin table, just write).")
    args = ap.parse_args()

    templates = template_registry.list_templates(published_only=not args.include_drafts)
    if args.template_id:
        templates = [t for t in templates if t["id"] == args.template_id]
        if not templates:
            print(f"template_not_found (or not published; try --include-drafts): {args.template_id}")
            return 2

    price_usd = args.price / args.coins_per_dollar
    print(f"\nFLAT PRICE: {args.price} coins = ${price_usd:.2f}/video | {args.coins_per_dollar:g} coins = $1")
    print(f"COGS:  Kling ${args.kling_usd_per_sec:.3f}/sec (ceil) + NBP ${args.nbp_usd:.2f} + Replit ${args.replit_usd:.2f}")
    print(f"MODE:  {'APPLY (will write)' if args.apply else 'DRY-RUN (no writes)'}"
          f"{' | single: ' + args.template_id if args.template_id else ''}\n")

    rows = []
    for t in sorted(templates, key=lambda x: x["id"]):
        dur = None
        if not args.no_probe:
            a = t.get("assets") or {}
            url = a.get("preview_video_url") or a.get("driving_video_url")
            dur = probe_duration_sec(url) if url else None
        rows.append((t["id"], t.get("credit_cost"), dur))

    if not args.no_probe:
        hdr = f"{'template':30} {'dur':>6} {'old':>4} {'new':>5} {'price':>7} {'COGS':>6} {'margin':>7} {'mgn%':>5} {'net%':>5}"
        print(hdr); print("-" * len(hdr))
        nets, worst = [], None
        for tid, old, dur in rows:
            short = tid.replace("viral-dances-", "")
            if dur is None:
                print(f"{short:30} {'??':>6} {str(old):>4} {args.price:>5}  (no duration)")
                continue
            cogs = math.ceil(dur) * args.kling_usd_per_sec + args.nbp_usd + args.replit_usd
            margin = price_usd - cogs
            mgn = 100 * margin / price_usd
            net = price_usd * (1 - args.apple_cut) - cogs
            net_pct = 100 * net / price_usd
            nets.append(net_pct)
            if worst is None or cogs > worst[1]:
                worst = (short, cogs, net_pct)
            print(f"{short:30} {dur:5.1f}s {str(old):>4} {args.price:>5} ${price_usd:6.2f} ${cogs:5.2f} ${margin:6.2f} {mgn:4.0f}% {net_pct:4.0f}%")
        if nets:
            print("-" * len(hdr))
            print(f"templates: {len(nets)} | net (post-Apple) min/avg/max: "
                  f"{min(nets):.0f}% / {sum(nets)/len(nets):.0f}% / {max(nets):.0f}%")
            print(f"worst-case COGS: {worst[0]} ${worst[1]:.2f} → still {worst[2]:.0f}% net")
            print("✓ every template clears COGS after Apple's cut" if min(nets) > 0
                  else "⚠️ some templates are UNDERWATER")

    if args.apply:
        print(f"\nApplying credit_cost={args.price} ...")
        ok = 0
        for tid, _old, _dur in rows:
            try:
                template_registry.set_credit_cost(tid, args.price)
                ok += 1
            except Exception as e:
                print(f"  FAILED {tid}: {e}")
        print(f"wrote {ok}/{len(rows)} templates. (updated_at bumped → mobile sees new price)")
    else:
        print("\nDRY-RUN — nothing written. Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
