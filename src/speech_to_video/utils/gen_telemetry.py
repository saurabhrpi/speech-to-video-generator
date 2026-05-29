"""Durable per-generation telemetry → Firestore collection `gen_events`.

Why this exists: the in-memory job manager is ephemeral (1-hr TTL, lost on
restart) and the Replit console only surfaces HTTP access logs, so a failed
generation leaves no recoverable trace of *which* stage failed or how long
each stage took. This module writes one document per generation attempt to
Firestore at the terminal point of the pipeline (success or failure), so
post-mortems and reliability stats survive restarts and are queryable with the
same firebase-admin credentials the backend already uses (no log scraping).

Document shape (collection `gen_events`, auto-id):
    {
      "job_id":            str | None,
      "uid":               str | None,
      "template_id":       str | None,
      "pipeline":          str | None,    # "motion-transfer" | "scene-insertion"
      "outcome":           str,           # "success" | "kling_failed" | "timeout"
                                          #  | "submit_error" | "empty_result"
                                          #  | "nbp_error" | "error"
      "failure_stage":     str | None,    # phase that failed, e.g. "kling_motion_control"
      "error":             str | None,    # truncated error string
      "kling_task_id":     str | None,
      "kling_model_name":  str | None,
      "kling_mode":        str | None,
      "last_task_status":  str | None,    # timeout discriminator: "submitted" (hang)
                                          #  vs "processing" (slow-but-alive)
      "prep_ms":           int,           # selfie presign + NBP regen + composite upload
      "kling_ms":          int,           # Kling submit + poll, wall-clock
      "total_ms":          int,           # whole dispatch
      "created_at":        server timestamp,
    }

Contract: `record()` NEVER raises. Telemetry must not be able to fail a
generation. All errors are logged and swallowed.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_COLLECTION = "gen_events"

# Cap stored error strings so a giant Kling `raw` payload can't bloat a doc.
_MAX_ERROR_CHARS = 2000


def _db():
    """Firestore client, initializing firebase-admin on first call.

    Mirrors credit_store._db() so both share the one admin app.
    """
    from firebase_admin import firestore as fb_firestore

    from ..api.firebase_auth import _init_firebase_admin

    _init_firebase_admin()
    return fb_firestore.client()


def _stringify_error(error: Any) -> Optional[str]:
    if error is None:
        return None
    s = error if isinstance(error, str) else repr(error)
    if len(s) > _MAX_ERROR_CHARS:
        s = s[:_MAX_ERROR_CHARS] + "…[truncated]"
    return s


def record(
    *,
    outcome: str,
    template_id: Optional[str] = None,
    pipeline: Optional[str] = None,
    job_id: Optional[str] = None,
    uid: Optional[str] = None,
    failure_stage: Optional[str] = None,
    error: Any = None,
    kling_task_id: Optional[str] = None,
    kling_model_name: Optional[str] = None,
    kling_mode: Optional[str] = None,
    last_task_status: Optional[str] = None,
    prep_ms: Optional[int] = None,
    kling_ms: Optional[int] = None,
    total_ms: Optional[int] = None,
) -> None:
    """Best-effort write of one generation event. Never raises.

    `outcome` is the only required field — everything else is filled in as far
    as the pipeline got before terminating.
    """
    try:
        from firebase_admin import firestore as fb_firestore

        doc: Dict[str, Any] = {
            "job_id": job_id,
            "uid": uid,
            "template_id": template_id,
            "pipeline": pipeline,
            "outcome": outcome,
            "failure_stage": failure_stage,
            "error": _stringify_error(error),
            "kling_task_id": kling_task_id,
            "kling_model_name": kling_model_name,
            "kling_mode": kling_mode,
            "last_task_status": last_task_status,
            "prep_ms": int(prep_ms) if prep_ms is not None else None,
            "kling_ms": int(kling_ms) if kling_ms is not None else None,
            "total_ms": int(total_ms) if total_ms is not None else None,
            "created_at": fb_firestore.SERVER_TIMESTAMP,
        }
        _db().collection(_COLLECTION).add(doc)
        logger.info(
            "GEN_TELEMETRY outcome=%s template=%s pipeline=%s kling_task=%s "
            "kling_ms=%s total_ms=%s last_status=%s",
            outcome, template_id, pipeline, kling_task_id,
            kling_ms, total_ms, last_task_status,
        )
    except Exception:
        # Telemetry is strictly observational — swallow everything.
        logger.exception("gen_telemetry.record failed (swallowed)")
