from typing import Any, Dict, Optional

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.config import Settings, get_settings


class AIMLAPIClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.aimlapi_base_url.rstrip("/")
        # Separate sessions: POST (no retries), GET (with retries)
        self.session_post = requests.Session()
        self.session_get = requests.Session()
        for s in (self.session_post, self.session_get):
            s.headers.update(
            {
                "Authorization": f"Bearer {self.settings.aimlapi_api_key}",
                "Content-Type": "application/json",
            }
            )
        # Robust retries for GET/polling only
        get_retry = Retry(
            total=int(os.getenv("AIMLAPI_HTTP_RETRIES", "3")),
            connect=3,
            read=3,
            backoff_factor=float(os.getenv("AIMLAPI_HTTP_BACKOFF", "0.8")),
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        self.session_get.mount("https://", HTTPAdapter(max_retries=get_retry))
        self.session_get.mount("http://", HTTPAdapter(max_retries=get_retry))
        # POST: no automatic HTTP retries (we handle minimal retry manually)
        self.session_post.mount("https://", HTTPAdapter(max_retries=Retry(total=0)))
        self.session_post.mount("http://", HTTPAdapter(max_retries=Retry(total=0)))

    def generate_video(
        self,
        prompt: str,
        duration: int,
        quality: str,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        endpoint_path: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a generation using AIMLAPI v2 endpoint:
        POST {base_url}/generate/video/google/generation
        Body: {"model": "alibaba/wan2.1-t2v-turbo", "prompt": "..."}
        """
        import time

        url = f"{self.base_url.rstrip('/')}{(endpoint_path or self.settings.aimlapi_generate_path)}"
        body: Dict[str, Any] = {
            "model": model or "alibaba/wan2.1-t2v-turbo",
            "prompt": prompt,
        }
        if seed is not None:
            body["seed"] = int(seed)
        # Duration hint (used by Veo; ignored by some providers)
        if isinstance(duration, int) and duration > 0:
            body["duration"] = int(duration)
        if aspect_ratio:
            body["aspect_ratio"] = aspect_ratio
        if resolution:
            body["resolution"] = resolution

        last: Dict[str, Any] = {}
        attempts = int(os.getenv("AIMLAPI_POST_ATTEMPTS", "2"))
        backoff = 1.0
        for _ in range(attempts):
            try:
                connect_to = float(os.getenv("AIMLAPI_CONNECT_TIMEOUT", "10"))
                read_to = float(os.getenv("AIMLAPI_READ_TIMEOUT", "45"))
                resp = self.session_post.post(url, json=body, timeout=(connect_to, read_to))
                try:
                    data = resp.json()
                except Exception:
                    data = {"error": resp.text}
                data["_status_code"] = resp.status_code
                data["_attempt_url"] = url
                if resp.status_code not in {429} and resp.status_code < 500:
                    return data
                last = data
            except requests.Timeout as e:
                last = {"error": f"timeout: {e}", "_status_code": 0, "_attempt_url": url}
            except requests.RequestException as e:
                last = {"error": f"request_error: {e}", "_status_code": 0, "_attempt_url": url}
            time.sleep(backoff)
            backoff *= 2.0
        return last or {"error": "No response", "_status_code": 0}

    def get_status(self, job_id: str, status_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Poll generation using AIMLAPI v2 endpoint:
        GET {base_url}/generate/video/google/generation?generation_id={id}
        """
        import time

        # Support both query style and REST style (e.g., /video/generations/{id})
        base = self.base_url.rstrip('/')
        if status_path and "{id}" in status_path:
            jid = str(job_id)
            # Some providers return IDs like "<uuid>:<model>"; REST paths expect the UUID only
            id_only = jid.split(":")[0]
            url = f"{base}{status_path.format(id=id_only)}"
            params = None
        else:
            url = f"{base}{(status_path or self.settings.aimlapi_status_path)}"
            params = {self.settings.aimlapi_status_query_param: job_id}
        last: Dict[str, Any] = {}
        attempts = int(os.getenv("AIMLAPI_STATUS_ATTEMPTS", "2"))
        backoff = 1.0
        for _ in range(attempts):
            try:
                connect_to = float(os.getenv("AIMLAPI_CONNECT_TIMEOUT", "10"))
                read_to = float(os.getenv("AIMLAPI_STATUS_READ_TIMEOUT", "30"))
                if params is None:
                    resp = self.session_get.get(url, timeout=(connect_to, read_to))
                else:
                    resp = self.session_get.get(url, params=params, timeout=(connect_to, read_to))
                try:
                    data = resp.json()
                except Exception:
                    data = {"error": resp.text}
                data["_status_code"] = resp.status_code
                data["_attempt_url"] = resp.url
                if resp.status_code not in {429} and resp.status_code < 500:
                    return data
                last = data
            except requests.Timeout as e:
                last = {"error": f"timeout: {e}", "_status_code": 0, "_attempt_url": url}
            except requests.RequestException as e:
                last = {"error": f"request_error: {e}", "_status_code": 0, "_attempt_url": url}
            time.sleep(backoff)
            backoff *= 2.0
        return last or {"error": "No response", "_status_code": 0}

    def poll_until_complete(self, job_id: str, max_wait: int = 300, interval: int = 5, status_path: Optional[str] = None) -> Dict[str, Any]:
        import time

        env_max = int(os.getenv("AIMLAPI_MAX_WAIT_SECONDS", str(max_wait)))
        env_int = int(os.getenv("AIMLAPI_POLL_INTERVAL_SECONDS", str(interval)))
        max_wait = env_max
        interval = env_int
        start = time.time()
        while time.time() - start < max_wait:
            status = self.get_status(job_id, status_path=status_path)
            state = (status.get("status") or "").lower()
            # Fallbacks for providers that don't support REST GET yet
            if status.get("_status_code") == 404:
                # Try query-style on /video/generations
                try:
                    qstatus = self.get_status(job_id, status_path="/video/generations")
                    if qstatus and int(qstatus.get("_status_code", 0)) < 400:
                        status = qstatus
                        state = (status.get("status") or "").lower()
                    else:
                        # Try legacy google status endpoint
                        qstatus2 = self.get_status(job_id, status_path="/generate/video/google/generation")
                        if qstatus2 and int(qstatus2.get("_status_code", 0)) < 400:
                            status = qstatus2
                            state = (status.get("status") or "").lower()
                except Exception:
                    pass
                if status.get("_status_code") == 404 and not status.get("status"):
                    time.sleep(interval)
                    continue
            if state in {"failed", "error"}:
                return status
            # common in-progress states from sample
            if state in {"waiting", "active", "queued", "generating"}:
                time.sleep(interval)
                continue
            # If status is something else or a URL is present, treat as done
            url = self._extract_video_url(status)
            if url or state in {"completed", "succeeded", "finished"}:
                return status
            time.sleep(interval)
        return {"status": "timeout", "error": "Generation timed out", "last_seen": status if 'status' in locals() else None}

    def _get_resolution(self, quality: str) -> str:
        if quality == "high":
            return self.settings.default_resolution_high
        return self.settings.default_resolution_medium

    def _extract_video_url(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract a playable media URL from provider responses.
        Avoid returning provider status/API URLs (e.g., /generation?...).
        """
        from urllib.parse import urlparse

        urls: list[str] = []

        def _walk(obj):
            if isinstance(obj, str) and obj.startswith("http"):
                urls.append(obj)
                return
            if isinstance(obj, dict):
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for it in obj:
                    _walk(it)

        _walk(data)

        if not urls:
            return None
        # Strict: only return direct media links (tolerate query strings)
        for u in urls:
            try:
                from urllib.parse import urlparse
                path = urlparse(u).path.lower()
                if path.endswith(".mp4") or path.endswith(".webm"):
                    return u
            except Exception:
                pass
            lu = u.lower()
            import re
            if re.search(r"\.(mp4|webm)(\?|$)", lu):
                return u
        return None


