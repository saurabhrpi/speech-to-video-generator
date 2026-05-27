"""Flip a template's published_status with an audit log entry (AIV-82).

Primary admin path for V2 launch — replaces editing the doc in the Firebase
Console (Console edits bypass `template_status_log` and are NOT logged).

Publishing is gated on a first-frame poster (S81): a template can only go to
`published` once `assets.thumbnail_url` is usable. If it's missing, this script
generates it (frame 0 of preview_stream.mp4) before flipping; it refuses with
exit code 3 only if the poster can't be made (preview_stream.mp4 not on R2).
This makes "no template ships posterless" an invariant of the publish path,
independent of how the doc was seeded.

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

    # Poster gate (S81): no template ships posterless. On publish, require a
    # usable first-frame thumbnail; if missing, generate it here (covers a
    # template seeded by an older no-thumbnail seed, or one whose seed-time
    # poster step failed). Refuse only if generation is impossible — that means
    # preview_stream.mp4 isn't on R2 yet. Enforced regardless of HOW the doc was
    # seeded, so it also covers future non-dance template types.
    if args.status == template_registry.STATUS_PUBLISHED:
        from src.speech_to_video.utils.template_thumbnail import (
            generate_thumbnail,
            is_usable_thumbnail,
        )

        if not is_usable_thumbnail((before.get("assets") or {}).get("thumbnail_url")):
            log.info("%s has no usable thumbnail_url — generating poster before publish...", args.template_id)
            result = generate_thumbnail(before, force=True)
            if result != "ok":
                log.error(
                    "refusing to publish %s: no usable thumbnail and auto-generation %r "
                    "(need preview_stream.mp4 on R2). Backfill then retry:\n"
                    "  .venv/bin/python scripts/generate_template_thumbnails.py --template-id %s",
                    args.template_id, result, args.template_id,
                )
                return 3

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
