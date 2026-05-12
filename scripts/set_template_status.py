"""Flip a template's published_status with an audit log entry (AIV-82).

Primary admin path for V2 launch — replaces editing the doc in the Firebase
Console (Console edits bypass `template_status_log` and are NOT logged).

Usage:
    python scripts/set_template_status.py <template_id> <draft|qa-pending|published> [--reason ...]

Examples:
    python scripts/set_template_status.py viral-dances-bombale published
    python scripts/set_template_status.py viral-dances-bombale qa-pending --reason "user_flag_threshold_0.3"
    python scripts/set_template_status.py viral-dances-bombale draft
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils import template_registry  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("set_template_status")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template_id")
    parser.add_argument(
        "status",
        choices=sorted(
            (
                template_registry.STATUS_DRAFT,
                template_registry.STATUS_QA_PENDING,
                template_registry.STATUS_PUBLISHED,
            )
        ),
    )
    parser.add_argument("--reason", default=None, help="Optional free-text context recorded in the audit log.")
    args = parser.parse_args()

    try:
        before = template_registry.get_template(args.template_id)
    except template_registry.TemplateNotFound:
        log.error("template_not_found: %s", args.template_id)
        return 2

    from_status = before.get("published_status")
    if from_status == args.status:
        log.info("%s already %s — flipping anyway (logs admin intent).", args.template_id, args.status)

    after = template_registry.set_status(
        args.template_id,
        args.status,
        actor="cli",
        reason=args.reason,
    )

    log.info(
        "%s: %s -> %s%s",
        args.template_id,
        from_status,
        after.get("published_status"),
        f" (reason: {args.reason})" if args.reason else "",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
