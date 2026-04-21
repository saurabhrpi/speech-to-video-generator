import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()
_MAX_JOBS = 50
_JOB_TTL = 3600


def create_job() -> str:
    job_id = str(uuid.uuid4())
    now = time.time()
    with _lock:
        if len(_jobs) > _MAX_JOBS:
            cutoff = now - _JOB_TTL
            stale = [jid for jid, j in _jobs.items() if j.get("created_at", 0) < cutoff]
            for jid in stale:
                del _jobs[jid]
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
