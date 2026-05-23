"""Toggle the GLOBAL Kling runtime model + mode (S74, AIV-101).

Backend reads model_name + mode from Firestore `config/runtime` with a 30s
in-memory cache. Flips here take effect within ~30s of the write — no code
deploy needed.

Per-template overrides (which win over global) live in their own script:
  scripts/set_template_kling_override.py

Usage:
    # Show current global state + the hardcoded fallback baseline
    .venv/bin/python scripts/set_kling_runtime.py --show

    # Flip via preset (preferred)
    .venv/bin/python scripts/set_kling_runtime.py --preset v3-pro
    .venv/bin/python scripts/set_kling_runtime.py --preset v2-6-std

    # Or explicit
    .venv/bin/python scripts/set_kling_runtime.py --model kling-v3 --mode pro

    # Partial (model only or mode only)
    .venv/bin/python scripts/set_kling_runtime.py --mode pro
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PRESETS = {
    "v3-pro":   {"model_name": "kling-v3",   "mode": "pro"},
    "v3-std":   {"model_name": "kling-v3",   "mode": "std"},
    "v2-6-pro": {"model_name": "kling-v2-6", "mode": "pro"},
    "v2-6-std": {"model_name": "kling-v2-6", "mode": "std"},
}

VALID_MODELS = {"kling-v2-6", "kling-v3"}
VALID_MODES = {"std", "pro"}


def main() -> int:
    ap = argparse.ArgumentParser()
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--show", action="store_true", help="Print current state, no write")
    grp.add_argument("--preset", choices=sorted(PRESETS.keys()), help="Apply a named preset")
    grp.add_argument("--model", choices=sorted(VALID_MODELS), help="Set kling_model_name only")
    ap.add_argument("--mode", choices=sorted(VALID_MODES), help="Set kling_mode (combine with --model, or use alone)")
    args = ap.parse_args()

    if args.preset:
        target = PRESETS[args.preset]
    elif args.model or args.mode:
        target = {}
        if args.model:
            target["model_name"] = args.model
        if args.mode:
            target["mode"] = args.mode
    else:
        target = None  # --show

    from src.speech_to_video.utils import runtime_config  # noqa: E402

    raw_before = runtime_config.show_kling_runtime_raw()
    effective_before = runtime_config.get_kling_runtime()
    log.info("raw doc       : %s", raw_before or "(unset; backend will use defaults)")
    log.info("effective now : model_name=%s mode=%s",
             effective_before["model_name"], effective_before["mode"])

    if args.show:
        return 0

    write_kwargs = {}
    if "model_name" in target:
        write_kwargs["model_name"] = target["model_name"]
    if "mode" in target:
        write_kwargs["mode"] = target["mode"]

    after = runtime_config.set_kling_runtime(**write_kwargs)
    log.info("wrote         : %s", {k: v for k, v in after.items() if k != "updated_at"})
    effective_after = runtime_config.get_kling_runtime()
    log.info("effective now : model_name=%s mode=%s",
             effective_after["model_name"], effective_after["mode"])
    log.info("(takes up to 30s to propagate to all backend instances via cache TTL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
