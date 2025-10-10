from typing import Any, Dict, Optional

import requests

from ..utils.config import Settings, get_settings


class AIMLAPIClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.aimlapi_base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.settings.aimlapi_api_key}",
                "Content-Type": "application/json",
            }
        )

    def generate_video(self, prompt: str, duration: int, quality: str) -> Dict[str, Any]:
        """
        Create a generation using AIMLAPI v2 endpoint:
        POST {base_url}/generate/video/google/generation
        Body: {"model": "alibaba/wan2.1-t2v-turbo", "prompt": "..."}
        """
        import time

        url = f"{self.base_url.rstrip('/')}{self.settings.aimlapi_generate_path}"
        body = {
            "model": "alibaba/wan2.1-t2v-turbo",
            "prompt": prompt,
        }

        last: Dict[str, Any] = {}
        backoff = 1.0
        for _ in range(3):
            resp = self.session.post(url, json=body, timeout=60)
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            data["_status_code"] = resp.status_code
            data["_attempt_url"] = url
            if resp.status_code not in {429} and resp.status_code < 500:
                return data
            last = data
            time.sleep(backoff)
            backoff *= 2.0
        return last or {"error": "No response", "_status_code": 0}

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Poll generation using AIMLAPI v2 endpoint:
        GET {base_url}/generate/video/google/generation?generation_id={id}
        """
        import time

        url = f"{self.base_url.rstrip('/')}{self.settings.aimlapi_status_path}"
        params = {self.settings.aimlapi_status_query_param: job_id}
        last: Dict[str, Any] = {}
        backoff = 1.0
        for _ in range(3):
            resp = self.session.get(url, params=params, timeout=30)
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            data["_status_code"] = resp.status_code
            data["_attempt_url"] = resp.url
            if resp.status_code not in {429} and resp.status_code < 500:
                return data
            last = data
            time.sleep(backoff)
            backoff *= 2.0
        return last or {"error": "No response", "_status_code": 0}

    def poll_until_complete(self, job_id: str, max_wait: int = 300, interval: int = 5) -> Dict[str, Any]:
        import time

        start = time.time()
        while time.time() - start < max_wait:
            status = self.get_status(job_id)
            state = (status.get("status") or "").lower()
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
        return {"status": "timeout", "error": "Generation timed out"}

    def _get_resolution(self, quality: str) -> str:
        if quality == "high":
            return self.settings.default_resolution_high
        return self.settings.default_resolution_medium

    def _extract_video_url(self, data: Dict[str, Any]) -> Optional[str]:
        # Find the first http(s) URL string in the response
        def _walk(obj):
            if isinstance(obj, str) and obj.startswith("http"):
                return obj
            if isinstance(obj, dict):
                for v in obj.values():
                    found = _walk(v)
                    if found:
                        return found
            if isinstance(obj, list):
                for item in obj:
                    found = _walk(item)
                    if found:
                        return found
            return None

        return _walk(data)


