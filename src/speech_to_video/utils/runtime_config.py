"""Firestore-backed runtime config with in-memory TTL cache (S74, AIV-101).

Holds knobs we want to flip without a code deploy (currently: Kling model_name
and mode). Reads are cached for 30s to keep Firestore round-trips out of the
request hot path; cache is invalidated automatically on writes through this
module's `set_kling_runtime`.

Fallbacks: if Firestore is unreachable or the doc is missing, returns the
hardcoded baseline. A Firestore outage degrades to "behavior before this file
existed" rather than breaking the template-video request path.

Per-template overrides resolve elsewhere (see VideoService._resolve_kling_settings);
this module only owns the GLOBAL config.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional

log = logging.getLogger(__name__)

_COLLECTION = "config"
_DOC_ID = "runtime"
_CACHE_TTL_S = 30.0

# Hardcoded fallback if Firestore is unreachable or the doc is missing.
# MUST stay aligned with a safe default — currently S73's runtime baseline.
# This means a first deploy (before the doc is written) behaves identically
# to the pre-AIV-101 hardcoded path.
_DEFAULTS = {
    "kling_model_name": "kling-v2-6",
    "kling_mode": "std",
}

_cache_value: Optional[Dict[str, str]] = None
_cache_expires_at: float = 0.0
_cache_lock = threading.Lock()


def _doc_ref():
    from firebase_admin import firestore as fb_firestore
    from ..api.firebase_auth import _init_firebase_admin
    _init_firebase_admin()
    db = fb_firestore.client()
    return db.collection(_COLLECTION).document(_DOC_ID)


def get_kling_runtime() -> Dict[str, str]:
    """Returns {"model_name": str, "mode": str} for runtime Kling calls.

    30s in-memory cache; falls back to hardcoded defaults on any Firestore
    error so a transient outage never breaks the request path.
    """
    global _cache_value, _cache_expires_at

    now = time.monotonic()
    with _cache_lock:
        if _cache_value is not None and now < _cache_expires_at:
            return _cache_value

    merged = _DEFAULTS.copy()
    try:
        snap = _doc_ref().get()
        if snap.exists:
            data = snap.to_dict() or {}
            if data.get("kling_model_name"):
                merged["kling_model_name"] = data["kling_model_name"]
            if data.get("kling_mode"):
                merged["kling_mode"] = data["kling_mode"]
    except Exception:
        log.exception("runtime_config Firestore read failed; using defaults")

    result = {
        "model_name": merged["kling_model_name"],
        "mode": merged["kling_mode"],
    }

    with _cache_lock:
        _cache_value = result
        _cache_expires_at = now + _CACHE_TTL_S
    return result


def invalidate_cache() -> None:
    """Force the next get_kling_runtime() to re-read Firestore. Called
    automatically by set_kling_runtime(); also useful in tests."""
    global _cache_value, _cache_expires_at
    with _cache_lock:
        _cache_value = None
        _cache_expires_at = 0.0


def set_kling_runtime(
    model_name: Optional[str] = None,
    mode: Optional[str] = None,
) -> Dict:
    """Partial Firestore update of config/runtime. Either or both may be
    passed; the other field is left untouched. Returns the post-write doc.

    Note: only invalidates THIS process's cache. Other backend instances
    (if we run >1 in prod) will pick up the change on their next 30s
    expiry — that's the intentional cache contract."""
    from firebase_admin import firestore as fb_firestore

    update: Dict = {}
    if model_name is not None:
        update["kling_model_name"] = model_name
    if mode is not None:
        update["kling_mode"] = mode
    if not update:
        raise ValueError("at least one of model_name or mode must be provided")
    update["updated_at"] = fb_firestore.SERVER_TIMESTAMP

    _doc_ref().set(update, merge=True)
    invalidate_cache()
    snap = _doc_ref().get()
    return snap.to_dict() or {}


def show_kling_runtime_raw() -> Dict:
    """Read the raw doc state, bypassing cache. Used by --show CLI commands."""
    snap = _doc_ref().get()
    return snap.to_dict() or {}
