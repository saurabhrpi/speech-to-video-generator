"""Firestore-backed template registry for V2 generate_template_video().

Each template lives at `templates/{template_id}` (e.g. `templates/viral-dances-bombale`).
Templates drive the V2 dispatch layer (AIV-14) + mobile carousel (AIV-30 / AIV-83).

Document shape:
    {
      "pipeline_class": "motion-transfer" | "scene-insertion",
      "outcome": "1" | "2" | "n/a",
      "category": str,                         # e.g. "viral_dances"
      "title": str,                            # carousel display, English only at V2
      "description": str,                      # carousel sub-copy, English only at V2
      "published_status": "draft" | "qa-pending" | "published",
      "assets": {
        "driving_video_url": str | None,       # Pipeline A: drives motion onto selfie.
                                               # Pipeline B: motion reference applied to composite.
        "scene_image_url": str | None,         # Pipeline B
        "thumbnail_url": str | None,           # carousel tile
        "preview_video_url": str | None,       # short hover loop, optional
      },
      "model": str,                            # e.g. "kling-2.6-motion-control-image"
      "credit_cost": int,                      # locked at 23 per AIV-36
      "prompt_template": str | None,           # Pipeline B Nano Banana Edit input
      "created_at": server timestamp,
      "updated_at": server timestamp,
    }

Schema locked S60 (2026-05-09); see AIV-10. No i18n at V2 launch. No version
history at the registry layer — create new template entries (e.g. `bombale-v2`)
when assets change.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_COLLECTION = "templates"
_STATUS_LOG_COLLECTION = "template_status_log"

PIPELINE_MOTION_TRANSFER = "motion-transfer"
PIPELINE_SCENE_INSERTION = "scene-insertion"
_VALID_PIPELINE_CLASSES = {PIPELINE_MOTION_TRANSFER, PIPELINE_SCENE_INSERTION}

OUTCOME_INTO_SCENE = "1"
OUTCOME_ONTO_CHARACTER = "2"
OUTCOME_NA = "n/a"
_VALID_OUTCOMES = {OUTCOME_INTO_SCENE, OUTCOME_ONTO_CHARACTER, OUTCOME_NA}

STATUS_DRAFT = "draft"
STATUS_QA_PENDING = "qa-pending"
STATUS_PUBLISHED = "published"
_VALID_STATUSES = {STATUS_DRAFT, STATUS_QA_PENDING, STATUS_PUBLISHED}


class TemplateNotFound(Exception):
    """Raised when a template_id has no Firestore doc."""

    def __init__(self, template_id: str):
        self.template_id = template_id
        super().__init__(f"template_not_found: {template_id}")


def _db():
    from firebase_admin import firestore as fb_firestore

    from ..api.firebase_auth import _init_firebase_admin

    _init_firebase_admin()
    return fb_firestore.client()


def _doc_ref(template_id: str):
    return _db().collection(_COLLECTION).document(template_id)


def get_template(template_id: str) -> Dict:
    """Load a single template by id. Raises TemplateNotFound if absent."""
    snap = _doc_ref(template_id).get()
    if not snap.exists:
        raise TemplateNotFound(template_id)
    data = snap.to_dict() or {}
    data["id"] = template_id
    return data


def list_templates(published_only: bool = True) -> List[Dict]:
    """List templates, optionally filtered to published_status=published.

    Returned in arbitrary order — carousel layer sorts/groups itself.
    """
    coll = _db().collection(_COLLECTION)
    query = (
        coll.where("published_status", "==", STATUS_PUBLISHED)
        if published_only
        else coll
    )
    out: List[Dict] = []
    for snap in query.stream():
        data = snap.to_dict() or {}
        data["id"] = snap.id
        out.append(data)
    return out


def upsert_template(template_id: str, data: Dict) -> Dict:
    """Create or fully replace a template doc. Returns the post-write state.

    `data` must contain the schema fields at module top EXCEPT `id`,
    `created_at`, `updated_at` (managed here). On update, `created_at` is
    preserved from the existing doc.
    """
    from firebase_admin import firestore as fb_firestore

    _validate(data)

    ref = _doc_ref(template_id)
    snap = ref.get()
    payload = dict(data)
    payload["updated_at"] = fb_firestore.SERVER_TIMESTAMP
    if snap.exists:
        existing = snap.to_dict() or {}
        if "created_at" in existing:
            payload["created_at"] = existing["created_at"]
        ref.set(payload)
    else:
        payload["created_at"] = fb_firestore.SERVER_TIMESTAMP
        ref.set(payload)

    out = ref.get().to_dict() or {}
    out["id"] = template_id
    return out


def set_status(
    template_id: str,
    status: str,
    actor: str = "unknown",
    uid: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict:
    """Update `published_status` and append an audit log entry atomically.

    The template doc update and the `template_status_log` write commit in one
    Firestore batch — neither lands without the other. Callers:
      - CLI (`scripts/set_template_status.py`) -> actor="cli"
      - AIV-47 quality auto-pause -> actor="auto-pause", reason=<rule>
      - Future admin dashboard -> actor="admin", uid=<who>

    Firebase Console direct edits BYPASS this path and are NOT logged at V2
    launch. Treat the log as best-effort, not ground truth.
    """
    from firebase_admin import firestore as fb_firestore

    if status not in _VALID_STATUSES:
        raise ValueError(
            f"invalid status {status!r}; expected one of {_VALID_STATUSES}"
        )

    db = _db()
    template_ref = db.collection(_COLLECTION).document(template_id)
    snap = template_ref.get()
    if not snap.exists:
        raise TemplateNotFound(template_id)
    from_status = (snap.to_dict() or {}).get("published_status")

    log_ref = db.collection(_STATUS_LOG_COLLECTION).document()
    batch = db.batch()
    batch.update(
        template_ref,
        {
            "published_status": status,
            "updated_at": fb_firestore.SERVER_TIMESTAMP,
        },
    )
    batch.set(
        log_ref,
        {
            "template_id": template_id,
            "from_status": from_status,
            "to_status": status,
            "actor": actor,
            "uid": uid,
            "reason": reason,
            "ts": fb_firestore.SERVER_TIMESTAMP,
        },
    )
    batch.commit()

    out = template_ref.get().to_dict() or {}
    out["id"] = template_id
    return out


def list_status_log(
    template_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Return audit log entries, newest first. `template_id=None` spans all
    templates. Used by AIV-47 quality dashboard + admin debugging.

    When filtered by `template_id`, sorting is client-side to avoid a Firestore
    composite (template_id, ts) index. Per-template entry counts are expected
    to stay in the low hundreds; revisit if that ceases to hold.
    """
    from firebase_admin import firestore as fb_firestore

    coll = _db().collection(_STATUS_LOG_COLLECTION)
    if template_id is not None:
        snaps = list(coll.where("template_id", "==", template_id).stream())
        snaps.sort(key=lambda s: (s.to_dict() or {}).get("ts"), reverse=True)
        snaps = snaps[:limit]
    else:
        query = coll.order_by("ts", direction=fb_firestore.Query.DESCENDING).limit(limit)
        snaps = list(query.stream())

    out: List[Dict] = []
    for snap in snaps:
        data = snap.to_dict() or {}
        data["id"] = snap.id
        out.append(data)
    return out


def _delete_status_log_for(template_id: str) -> int:
    """Test/admin helper: hard-delete all log entries for a template_id.
    Returns the number of deleted entries. NOT used in normal app flow.
    """
    coll = _db().collection(_STATUS_LOG_COLLECTION)
    deleted = 0
    for snap in coll.where("template_id", "==", template_id).stream():
        snap.reference.delete()
        deleted += 1
    return deleted


def delete_template(template_id: str) -> bool:
    """Remove a template doc. Returns True if a doc existed."""
    ref = _doc_ref(template_id)
    snap = ref.get()
    if not snap.exists:
        return False
    ref.delete()
    return True


def _validate(data: Dict) -> None:
    pc = data.get("pipeline_class")
    if pc not in _VALID_PIPELINE_CLASSES:
        raise ValueError(
            f"invalid pipeline_class {pc!r}; expected one of {_VALID_PIPELINE_CLASSES}"
        )
    out = data.get("outcome")
    if out not in _VALID_OUTCOMES:
        raise ValueError(
            f"invalid outcome {out!r}; expected one of {_VALID_OUTCOMES}"
        )
    st = data.get("published_status")
    if st not in _VALID_STATUSES:
        raise ValueError(
            f"invalid published_status {st!r}; expected one of {_VALID_STATUSES}"
        )
    cc = data.get("credit_cost")
    if not isinstance(cc, int) or cc <= 0:
        raise ValueError(f"credit_cost must be positive int; got {cc!r}")
    for field in ("category", "title", "model"):
        if not data.get(field):
            raise ValueError(f"required field {field!r} is missing or empty")
    assets = data.get("assets") or {}
    if not isinstance(assets, dict):
        raise ValueError("assets must be a dict")
