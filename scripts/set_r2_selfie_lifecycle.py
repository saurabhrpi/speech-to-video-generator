"""Set R2 object-lifecycle rules that auto-delete user *input* images shortly
after a generation finishes — the privacy backstop for the inline purge.

Background: `video_service._dispatch_motion_transfer` deletes the raw selfie +
NBP regen image from R2 the moment a gen reaches a terminal state (best-effort).
This lifecycle rule is the BACKSTOP for inputs orphaned by a crash mid-gen. It
must (a) be short — our privacy promise is "deleted within 24h" — and (b) cover
EVERY prefix in the private selfies bucket that holds face data:
    selfies/{uid}/...       raw uploaded selfie   (upload_selfie)
    nbp-regen/{tmpl}/...     NBP regen character   (_nbp_regen_character)
    composites/{uid}/...     Pipeline B composite  (_dispatch_scene_insertion)

The prior rule was 30 days on `selfies/` ONLY — `nbp-regen/` (also face data)
was covered by nothing.

Default is DRY-RUN: prints the bucket's current lifecycle + the proposed rules
and exits without changing anything. Pass --apply to write them; it then reads
the config back to confirm. Unmanaged rules (any prefix outside the three above)
are kept verbatim — only the managed prefixes are replaced.

Usage:
    python scripts/set_r2_selfie_lifecycle.py                  # dry-run (default)
    python scripts/set_r2_selfie_lifecycle.py --apply          # write 1-day rules
    python scripts/set_r2_selfie_lifecycle.py --days 1 --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import r2_client  # noqa: E402
from src.speech_to_video.utils.config import get_settings  # noqa: E402

# Every prefix in the private selfies bucket that holds user face data.
MANAGED_PREFIXES = ["selfies/", "nbp-regen/", "composites/"]


def _rule_prefix(rule: dict) -> Optional[str]:
    """Extract a rule's prefix, tolerating the legacy `Prefix`, the modern
    `Filter.Prefix`, and the `Filter.And.Prefix` shapes."""
    if "Prefix" in rule:
        return rule["Prefix"]
    f = rule.get("Filter") or {}
    if "Prefix" in f:
        return f["Prefix"]
    return (f.get("And") or {}).get("Prefix")


def _build_managed_rules(days: int) -> list:
    # R2 scopes by the modern `Filter.Prefix` and SILENTLY DROPS a legacy
    # top-level `Prefix` (verified S85 — it stored prefix-less whole-bucket
    # rules). The earlier MalformedXML was from an empty `Filter: {}` on the
    # kept multipart rule, not from a populated Filter — so scope with
    # `Filter.Prefix` here and keep prefix-less rules verbatim (never `{}`).
    return [
        {
            "ID": f"expire-{p.rstrip('/')}-{days}d",
            "Filter": {"Prefix": p},
            "Status": "Enabled",
            "Expiration": {"Days": days},
        }
        for p in MANAGED_PREFIXES
    ]


def _resolve_s3():
    """Return (boto3_client, label). Lifecycle config is a bucket-ADMIN op the
    app's object-scoped token can't do, so prefer an admin token supplied via
    R2_ADMIN_ACCESS_KEY_ID / R2_ADMIN_SECRET_ACCESS_KEY (read straight from the
    environment so .env's override=True can't clobber them). Fall back to the
    app token (fine for a read on some buckets; AccessDenied on most config ops).
    """
    import os

    ak = os.environ.get("R2_ADMIN_ACCESS_KEY_ID")
    sk = os.environ.get("R2_ADMIN_SECRET_ACCESS_KEY")
    if ak and sk:
        s = get_settings()
        if not s.r2_account_id:
            raise r2_client.R2NotConfigured("R2_ACCOUNT_ID missing (needed for the endpoint)")
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=f"https://{s.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name="auto",
        )
        return client, "admin token (R2_ADMIN_*)"
    return r2_client._s3(), "app token (object-scoped — will AccessDenied on lifecycle)"


def _fmt(rule: dict, tag: str = "") -> str:
    days = (rule.get("Expiration") or {}).get("Days")
    expire = f"{days}d" if days is not None else "—"
    return (
        f"  id={str(rule.get('ID')):32} prefix={str(_rule_prefix(rule)):16} "
        f"status={rule.get('Status')} expire={expire}{tag}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--days", type=int, default=1, help="expire input objects after N days (default 1)")
    ap.add_argument("--bucket", default=None, help="override bucket (default: the selfies bucket)")
    ap.add_argument("--apply", action="store_true", help="write the rules (default: dry-run)")
    args = ap.parse_args()

    if args.days < 1:
        print("--days must be >= 1 (R2 minimum). Refusing.")
        return 2

    bucket = args.bucket or get_settings().r2_selfies_bucket
    try:
        s3, token_label = _resolve_s3()
    except r2_client.R2NotConfigured as e:
        print(f"R2 not configured: {e}")
        return 2
    print(f"Credentials: {token_label}")

    from botocore.exceptions import ClientError

    print(f"\nBucket: {bucket}")

    # 1. Read current config (absent → empty).
    try:
        current_rules = s3.get_bucket_lifecycle_configuration(Bucket=bucket).get("Rules", [])
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code.startswith("NoSuchLifecycleConfiguration"):
            current_rules = []
        elif code in ("AccessDenied", "Forbidden"):
            print(f"  AccessDenied reading lifecycle: {e}")
            print(
                "  → The app's R2 token is object-scoped (GetObject/PutObject/etc.) and\n"
                "    cannot read or write BUCKET lifecycle config. Run this with an\n"
                "    admin-scoped R2 token (R2 → Manage API tokens → Admin Read & Write),\n"
                "    or set the rules in the Cloudflare dashboard instead."
            )
            return 1
        else:
            print(f"  Failed to read current lifecycle: {e}")
            return 1

    print(f"--- current lifecycle ({len(current_rules)} rule(s)) ---")
    print("\n".join(_fmt(r) for r in current_rules) or "  (none)")

    # 2. Merge: replace any rule that targets a managed prefix OR carries one of
    # our managed-rule IDs (any expiry-days variant) — the ID match also cleans
    # up earlier prefix-less rules R2 mis-stored. Keep everything else verbatim
    # (e.g. the multipart rule, which R2 round-trips with no Prefix/Filter).
    managed = _build_managed_rules(args.days)
    managed_id_stems = tuple(f"expire-{p.rstrip('/')}-" for p in MANAGED_PREFIXES)

    def _is_managed(r: dict) -> bool:
        return (r.get("ID") or "").startswith(managed_id_stems) or _rule_prefix(r) in MANAGED_PREFIXES

    kept = [r for r in current_rules if not _is_managed(r)]
    dropped = [r for r in current_rules if _is_managed(r)]
    merged = kept + managed

    print(f"\n--- proposed lifecycle ({len(merged)} rule(s), {args.days}d expiry on inputs) ---")
    print("\n".join(_fmt(r) for r in kept))
    print("\n".join(_fmt(r, "  [managed]") for r in managed))
    if dropped:
        print(f"  (replacing managed-prefix rule(s): {[r.get('ID') for r in dropped]})")
    if kept:
        print(f"  (keeping {len(kept)} unmanaged rule(s) verbatim)")

    if not args.apply:
        print("\nDRY-RUN — nothing changed. Re-run with --apply to write these rules.")
        return 0

    # 3. Apply, then read back to confirm.
    try:
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket, LifecycleConfiguration={"Rules": merged},
        )
    except ClientError as e:
        print(f"\nPUT failed: {e}")
        return 1

    confirmed = s3.get_bucket_lifecycle_configuration(Bucket=bucket).get("Rules", [])
    print(f"\nAPPLIED. Bucket now has {len(confirmed)} rule(s):")
    print("\n".join(_fmt(r) for r in confirmed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
