import logging
import os
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)

# MiniMax model name mapping: AIMLAPI-style -> MiniMax direct API
_MODEL_MAP = {
    "minimax/hailuo-2.3": "MiniMax-Hailuo-2.3",
    "minimax/hailuo-02": "MiniMax-Hailuo-02",
    "minimax/hailuo-2.3-fast": "MiniMax-Hailuo-2.3",
}

BASE_URL = "https://api.minimax.io/v1"


class MiniMaxClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.api_key = self.settings.minimax_api_key

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        # Retries on polling GET requests
        get_retry = Retry(
            total=3, connect=3, read=3,
            backoff_factor=0.8,
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=get_retry))

    def _resolve_model(self, model: str) -> str:
        return _MODEL_MAP.get(model, model)

    def submit(
        self,
        prompt: str,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
    ) -> Dict[str, Any]:
        """Submit a video generation task. Returns {task_id, base_resp}."""
        url = f"{BASE_URL}/video_generation"
        body: Dict[str, Any] = {
            "model": self._resolve_model(model),
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": prompt_optimizer,
        }
        logger.info("[MiniMax] submit POST %s model=%s duration=%d resolution=%s",
                     url, body["model"], duration, resolution)

        try:
            resp = self.session.post(url, json=body, timeout=(10, 45))
            data = resp.json()
            data["_status_code"] = resp.status_code
            logger.info("[MiniMax] submit response: status=%s data=%s", resp.status_code, data)
            return data
        except requests.Timeout as e:
            logger.error("[MiniMax] submit timeout: %s", e)
            return {"error": f"timeout: {e}", "_status_code": 0}
        except requests.RequestException as e:
            logger.error("[MiniMax] submit request error: %s", e)
            return {"error": f"request_error: {e}", "_status_code": 0}

    def poll(self, task_id: str) -> Dict[str, Any]:
        """Query task status. Returns {status, file_id (on success), base_resp}."""
        url = f"{BASE_URL}/query/video_generation"
        params = {"task_id": task_id}

        try:
            resp = self.session.get(url, params=params, timeout=(10, 30))
            data = resp.json()
            data["_status_code"] = resp.status_code
            return data
        except requests.Timeout as e:
            return {"error": f"timeout: {e}", "_status_code": 0}
        except requests.RequestException as e:
            return {"error": f"request_error: {e}", "_status_code": 0}

    def get_download_url(self, file_id: str) -> Dict[str, Any]:
        """Retrieve a download URL for a completed video. URL expires in 1 hour."""
        url = f"{BASE_URL}/files/retrieve"
        params = {"file_id": file_id}

        try:
            resp = self.session.get(url, params=params, timeout=(10, 30))
            data = resp.json()
            data["_status_code"] = resp.status_code
            return data
        except requests.Timeout as e:
            return {"error": f"timeout: {e}", "_status_code": 0}
        except requests.RequestException as e:
            return {"error": f"request_error: {e}", "_status_code": 0}

    def generate_and_poll(
        self,
        prompt: str,
        model: str = "MiniMax-Hailuo-2.3",
        duration: int = 6,
        resolution: str = "768P",
        prompt_optimizer: bool = True,
        max_wait: int = 600,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        High-level: submit T2V job, poll until done, fetch download URL.
        Returns {"success": True, "video_url": "..."} or {"success": False, "error": ...}.
        """
        max_wait = int(os.getenv("MINIMAX_MAX_WAIT_SECONDS", str(max_wait)))
        poll_interval = int(os.getenv("MINIMAX_POLL_INTERVAL_SECONDS", str(poll_interval)))

        # Step 1: Submit
        submit_data = self.submit(
            prompt=prompt, model=model, duration=duration,
            resolution=resolution, prompt_optimizer=prompt_optimizer,
        )
        status_code = int(submit_data.get("_status_code", 0))
        base_resp = submit_data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            return {"success": False, "error": submit_data}
        if not (200 <= status_code < 300):
            return {"success": False, "error": submit_data}

        task_id = submit_data.get("task_id")
        if not task_id:
            return {"success": False, "error": "No task_id in response", "raw": submit_data}

        logger.info("[MiniMax] task_id=%s — polling (max %ds)", task_id, max_wait)

        # Step 2: Poll
        start = time.time()
        last_status = {}
        while time.time() - start < max_wait:
            last_status = self.poll(task_id)
            status = str(last_status.get("status", "")).lower()
            logger.debug("[MiniMax] poll task_id=%s status=%s", task_id, status)

            if status == "fail":
                return {"success": False, "error": last_status, "task_id": task_id}
            if status == "success":
                file_id = last_status.get("file_id")
                if not file_id:
                    return {"success": False, "error": "Success but no file_id", "raw": last_status, "task_id": task_id}

                # Step 3: Get download URL
                dl_data = self.get_download_url(file_id)
                dl_url = (dl_data.get("file", {}) or {}).get("download_url")
                if not dl_url:
                    # Try top-level
                    dl_url = dl_data.get("download_url")
                if dl_url:
                    logger.info("[MiniMax] video ready: task_id=%s file_id=%s", task_id, file_id)
                    return {"success": True, "video_url": dl_url, "task_id": task_id, "file_id": file_id}
                return {"success": False, "error": "No download_url in file response", "raw": dl_data, "task_id": task_id}

            # In progress: Preparing, Queueing, Processing
            time.sleep(poll_interval)

        return {
            "success": False,
            "error": "Generation timed out",
            "task_id": task_id,
            "last_status": last_status,
        }
