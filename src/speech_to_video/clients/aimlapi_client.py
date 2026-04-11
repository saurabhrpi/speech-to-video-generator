import logging
from typing import Any, Dict, List, Optional

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


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
        generate_audio: Optional[bool] = None,
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
        if generate_audio is not None:
            body["generate_audio"] = bool(generate_audio)

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

    def poll_until_complete(self, job_id: str, max_wait: int = 600, interval: int = 5, status_path: Optional[str] = None) -> Dict[str, Any]:
        import time

        env_max = int(os.getenv("AIMLAPI_MAX_WAIT_SECONDS", str(max_wait)))
        env_int = int(os.getenv("AIMLAPI_POLL_INTERVAL_SECONDS", str(interval)))
        max_wait = env_max
        interval = env_int
        start = time.time()
        while time.time() - start < max_wait:
            status = self.get_status(job_id, status_path=status_path)
            state = str(status.get("status") or "").lower()
            # Fallbacks for providers that don't support REST GET yet
            if status.get("_status_code") == 404:
                # Try query-style on /video/generations
                try:
                    qstatus = self.get_status(job_id, status_path="/video/generations")
                    if qstatus and int(qstatus.get("_status_code", 0)) < 400:
                        status = qstatus
                        state = str(status.get("status") or "").lower()
                    else:
                        # Try legacy google status endpoint
                        qstatus2 = self.get_status(job_id, status_path="/generate/video/google/generation")
                        if qstatus2 and int(qstatus2.get("_status_code", 0)) < 400:
                            status = qstatus2
                            state = str(status.get("status") or "").lower()
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

    def generate_image_to_video(
        self,
        image_url: str,
        prompt: str,
        model: Optional[str] = None,
        last_image_url: Optional[str] = None,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        camera_fixed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Generate a video from an image (and optionally a last-frame image).
        Supports Hailuo, Kling, Seedance, and other AIMLAPI I2V models.
        """
        import time

        base = self.settings.aimlapi_base_url.rstrip("/").replace("/v2", "")
        resolved_model = model or self.settings.i2v_model
        is_hailuo = "hailuo" in resolved_model.lower() or "minimax" in resolved_model.lower()
        is_seedance = "seedance" in resolved_model.lower()

        if is_hailuo:
            url = f"{base}/generate/video/minimax/generation"
            body: Dict[str, Any] = {
                "model": resolved_model,
                "prompt": prompt,
                "image_url": image_url,
                "enhance_prompt": False,
            }
            if last_image_url:
                body["last_image_url"] = last_image_url
            if duration:
                body["duration"] = int(duration)
            if resolution:
                body["resolution"] = resolution
        else:
            url = f"{base}/v2/video/generations"
            body = {
                "model": resolved_model,
                "prompt": prompt,
                "image_url": image_url,
            }
            if last_image_url:
                is_kling = "kling" in resolved_model.lower()
                key = "tail_image_url" if is_kling else "last_image_url"
                body[key] = last_image_url
            if duration:
                body["duration"] = int(duration)
            if resolution:
                body["resolution"] = resolution
            if is_seedance:
                body["watermark"] = False
                if camera_fixed is not None:
                    body["camerafixed"] = camera_fixed
            if "kling" in resolved_model.lower():
                body["generate_audio"] = False
                body["duration"] = 3

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

    def generate_and_poll_i2v(
        self,
        image_url: str,
        prompt: str,
        model: Optional[str] = None,
        last_image_url: Optional[str] = None,
        duration: Optional[int] = None,
        max_wait: int = 600,
        resolution: Optional[str] = None,
        camera_fixed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        High-level: submit I2V job (Hailuo, Kling, Seedance, etc.), poll until done, return video URL.
        """
        resolved_model = model or self.settings.i2v_model
        is_hailuo = "hailuo" in resolved_model.lower() or "minimax" in resolved_model.lower()

        data = self.generate_image_to_video(
            image_url, prompt, model=model,
            last_image_url=last_image_url, duration=duration,
            resolution=resolution, camera_fixed=camera_fixed,
        )
        status_code = int(data.get("_status_code", 0))
        if not (200 <= status_code < 300):
            return {"success": False, "error": data}

        job_id = data.get("id") or data.get("job_id") or data.get("generation_id")
        if not job_id:
            video_url = self._extract_video_url(data)
            if video_url:
                return {"success": True, "video_url": video_url}
            return {"success": False, "error": "No job_id in response", "raw": data}

        poll_path = "/generate/video/minimax/generation" if is_hailuo else "/v2/video/generations"
        poll_result = self.poll_until_complete(
            job_id=str(job_id),
            max_wait=max_wait,
            status_path=poll_path,
        )
        video_url = self._extract_video_url(poll_result)
        if video_url:
            return {"success": True, "video_url": video_url, "job_id": str(job_id)}
        return {"success": False, "error": poll_result, "job_id": str(job_id)}

    def generate_image(
        self,
        prompt: str,
        image_urls: Optional[List[str]] = None,
        model: Optional[str] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "1K",
    ) -> Dict[str, Any]:
        """
        Generate or edit an image via Nano Banana Pro / Pro Edit.

        Stage 1 (T2I): prompt only, model=google/nano-banana-pro
        Stages 2+ (Edit): prompt + image_urls, model=google/nano-banana-pro-edit
        """
        base = self.settings.aimlapi_base_url.rstrip("/").replace("/v2", "")
        url = f"{base}/v1/images/generations"

        if model is None:
            model = self.settings.nano_banana_edit_model if image_urls else self.settings.nano_banana_t2i_model

        body: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "num_images": 1,
        }
        if image_urls:
            body["image_urls"] = image_urls

        logger.info("[AIMLAPI] generate_image POST %s model=%s image_urls=%s", url, model, bool(image_urls))
        logger.debug("[AIMLAPI] generate_image body: %s", {k: v for k, v in body.items() if k != "prompt"})

        import time
        last: Dict[str, Any] = {}
        attempts = int(os.getenv("AIMLAPI_POST_ATTEMPTS", "2"))
        backoff = 1.0
        for _ in range(attempts):
            try:
                connect_to = float(os.getenv("AIMLAPI_CONNECT_TIMEOUT", "10"))
                read_to = float(os.getenv("AIMLAPI_IMAGE_READ_TIMEOUT", "120"))
                resp = self.session_post.post(url, json=body, timeout=(connect_to, read_to))
                try:
                    data = resp.json()
                except Exception:
                    data = {"error": resp.text}
                data["_status_code"] = resp.status_code
                logger.info("[AIMLAPI] generate_image response: status=%s", resp.status_code)
                logger.debug("[AIMLAPI] generate_image raw response: %s", data)

                if resp.status_code >= 400:
                    logger.error("[AIMLAPI] generate_image FAILED: http=%s body=%s", resp.status_code, data)
                    last = data
                    if resp.status_code not in {429} and resp.status_code < 500:
                        return {"success": False, "error": data}
                else:
                    image_url = self._extract_image_url(data)
                    if image_url:
                        logger.info("[AIMLAPI] generate_image OK: %s", image_url)
                        return {"success": True, "images": [image_url], "raw": data}
                    logger.warning("[AIMLAPI] generate_image: no image URL found in response: %s", data)
                    return {"success": False, "error": "No image URL in response", "raw": data}
            except requests.Timeout as e:
                last = {"error": f"timeout: {e}", "_status_code": 0}
                logger.error("[AIMLAPI] generate_image timeout: %s", e)
            except requests.RequestException as e:
                last = {"error": f"request_error: {e}", "_status_code": 0}
                logger.error("[AIMLAPI] generate_image request error: %s", e)
            time.sleep(backoff)
            backoff *= 2.0
        return {"success": False, "error": last or "No response"}

    def _extract_image_url(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract an image URL from the Nano Banana response."""
        if isinstance(data, dict):
            # Common pattern: {"data": [{"url": "..."}]}
            items = data.get("data") or data.get("images") or data.get("results") or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        u = item.get("url") or item.get("image_url") or item.get("uri")
                        if u and isinstance(u, str) and u.startswith("http"):
                            return u
                    elif isinstance(item, str) and item.startswith("http"):
                        return item
            # Flat: {"url": "..."}
            u = data.get("url") or data.get("image_url")
            if u and isinstance(u, str) and u.startswith("http"):
                return u
        return None

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


