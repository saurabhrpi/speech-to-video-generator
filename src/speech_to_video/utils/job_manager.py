import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()
_MAX_JOBS = 50
_JOB_TTL = 3600

_INFLIGHT_STATUSES = {"queued", "running"}


def inflight_jobs() -> List[Dict[str, Any]]:
    """Return lightweight summaries of jobs that would be orphaned by a
    container restart (status in {queued, running}). Used by the AIV-78
    observability logs to measure V2 orphan rate without persisting state.
    Order: oldest first, for grep stability."""
    now = time.time()
    with _lock:
        items = []
        for job_id, j in _jobs.items():
            if j.get("status") not in _INFLIGHT_STATUSES:
                continue
            items.append({
                "job_id": job_id,
                "uid": j.get("uid"),
                "status": j.get("status"),
                "phase": j.get("phase"),
                "credit_cost": j.get("credit_cost"),
                "is_anonymous": j.get("is_anonymous"),
                "age_s": int(now - (j.get("created_at") or now)),
            })
        items.sort(key=lambda x: x["age_s"], reverse=True)
        return items


def _gc_stale_locked(now: float) -> None:
    """Evict jobs older than TTL once we exceed MAX_JOBS. Caller must hold _lock."""
    if len(_jobs) > _MAX_JOBS:
        cutoff = now - _JOB_TTL
        stale = [jid for jid, j in _jobs.items() if j.get("created_at", 0) < cutoff]
        for jid in stale:
            del _jobs[jid]


def _is_unsettled_credit_job(job: Dict[str, Any]) -> bool:
    """A credit-bearing job that still owes a deduction.

    True for queued/running jobs, AND for completed jobs whose consume hasn't
    fired yet (the exact window the TOCTOU race exploited). False for failed
    jobs, jobs that returned {success: False, no video_url} (no consume due),
    and jobs whose credit was already consumed.
    """
    if int(job.get("credit_cost") or 0) <= 0:
        return False
    if job.get("credit_consumed"):
        return False
    status = job.get("status")
    if status == "failed":
        return False
    if status == "completed":
        result = job.get("result") or {}
        if not result.get("video_url"):
            return False
    return True


def create_job() -> str:
    job_id = str(uuid.uuid4())
    now = time.time()
    with _lock:
        _gc_stale_locked(now)
        _jobs[job_id] = {
            "status": "queued",
            "phase": None,
            "step": 0,
            "total_steps": 0,
            "message": "Queued",
            "result": None,
            "partial_result": None,
            "created_at": now,
            "usage_counted": False,
        }
    return job_id


def try_create_credit_job(uid: str, credit_cost: int, is_anonymous: bool) -> Optional[str]:
    """Atomically gate concurrent credit-bearing submits per uid.

    Returns a fresh job_id if this uid has no unsettled credit-bearing job;
    returns None if one is already in flight. The check + create runs under
    _lock so two concurrent callers cannot both win.
    """
    now = time.time()
    job_id = str(uuid.uuid4())
    with _lock:
        _gc_stale_locked(now)
        for j in _jobs.values():
            if j.get("uid") != uid:
                continue
            if _is_unsettled_credit_job(j):
                return None
        _jobs[job_id] = {
            "status": "queued",
            "phase": None,
            "step": 0,
            "total_steps": 0,
            "message": "Queued",
            "result": None,
            "partial_result": None,
            "created_at": now,
            "usage_counted": False,
            "uid": uid,
            "is_anonymous": bool(is_anonymous),
            "credit_cost": int(credit_cost),
        }
    return job_id


def update_job(job_id: str, **kwargs: Any) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(kwargs)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        if job_id in _jobs:
            return dict(_jobs[job_id])
    return None


def try_claim(job_id: str, field: str) -> bool:
    """Atomic compare-and-set: return True only if `field` was falsy and we flipped it to True.

    Gives exactly-once semantics for side-effects that must run once per job
    (e.g. deducting credits on completion), even when multiple pollers race.
    """
    with _lock:
        job = _jobs.get(job_id)
        if not job or job.get(field):
            return False
        job[field] = True
        return True


def start_job(job_id: str, fn: Callable, *args: Any, **kwargs: Any) -> threading.Thread:
    def wrapper():
        update_job(job_id, status="running")
        try:
            result = fn(*args, **kwargs)
            update_job(job_id, status="completed", result=result, message="Done")
        except Exception as exc:
            logger.exception("[JobManager] Job %s failed with exception", job_id)
            update_job(
                job_id,
                status="failed",
                result={"success": False, "error": str(exc)},
                message=f"Failed: {exc}",
            )

    t = threading.Thread(target=wrapper, daemon=True)
    t.start()
    return t
