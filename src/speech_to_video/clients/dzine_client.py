import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)

_MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG": "png",
    b"GIF8": "gif",
    b"RIFF": "webp",  # RIFF....WEBP — checked further below
}


def detect_image_format(data: bytes) -> str:
    """Return a MIME-safe image subtype (jpeg, png, webp, gif) from raw bytes."""
    for magic, fmt in _MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            if fmt == "webp" and data[8:12] != b"WEBP":
                continue
            return fmt
    return "png"


class DzineClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.dzine_base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.settings.dzine_api_key,
            "Content-Type": "application/json",
        })
        retry = Retry(
            total=3, connect=3, read=3,
            backoff_factor=0.8,
            status_forcelist=(429, 502, 503, 504),
            allowed_methods=("GET", "POST"),
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def text_to_image(
        self,
        prompt: str,
        seed: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
        style_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/create_task_txt2img"
        body: Dict[str, Any] = {
            "prompt": prompt,
            "generate_slots": [1, 0, 0, 0],
            "style_code": style_code or self.settings.dzine_style_code,
            "style_intensity": 1,
            "quality_mode": 0,
            "target_w": width,
            "target_h": height,
        }
        if seed is not None:
            body["seed"] = int(seed)

        logger.info("[Dzine] text_to_image POST %s", url)
        logger.debug("[Dzine] text_to_image body: %s", {k: v for k, v in body.items() if k != "prompt"})
        resp = self.session.post(url, json=body, timeout=(10, 60))
        logger.info("[Dzine] text_to_image response: status=%s", resp.status_code)
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
            logger.error("[Dzine] text_to_image non-JSON response: %s", resp.text[:500])
        logger.debug("[Dzine] text_to_image raw response: %s", data)
        data["_status_code"] = resp.status_code

        dzine_code = data.get("code")
        if resp.status_code >= 400 or (dzine_code is not None and int(dzine_code) != 200):
            logger.error("[Dzine] text_to_image FAILED: http=%s dzine_code=%s msg=%s", resp.status_code, dzine_code, data.get("msg") or data.get("detail") or data)
        else:
            logger.info("[Dzine] text_to_image OK: task_id=%s", data.get("data", {}).get("task_id") or data.get("task_id"))
        return data

    def image_to_image(
        self,
        prompt: str,
        reference_image_url: Optional[str] = None,
        reference_image_bytes: Optional[bytes] = None,
        image_format: str = "png",
        seed: Optional[int] = None,
        style_code: Optional[str] = None,
        structure_match: Optional[float] = None,
        color_match: Optional[float] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/create_task_img2img"

        if reference_image_url:
            images_payload = [{"url": reference_image_url}]
            ref_desc = f"url={reference_image_url}"
        elif reference_image_bytes:
            b64 = base64.b64encode(reference_image_bytes).decode("utf-8")
            mime = f"image/{image_format}"
            images_payload = [{"base64_data": f"data:{mime};base64,{b64}"}]
            ref_desc = f"base64 {len(reference_image_bytes)} bytes, mime={mime}"
        else:
            return {"error": "No reference image provided", "_status_code": 0}

        body: Dict[str, Any] = {
            "prompt": prompt,
            "style_code": style_code or self.settings.dzine_style_code,
            "style_intensity": 0.9,
            "structure_match": structure_match if structure_match is not None else self.settings.dzine_structure_match,
            "color_match": int(color_match if color_match is not None else self.settings.dzine_color_match),
            "quality_mode": 0,
            "generate_slots": [1, 0, 0, 0],
            "face_match": 0,
            "images": images_payload,
        }
        if seed is not None:
            body["seed"] = int(seed)

        logger.info("[Dzine] image_to_image POST %s (ref: %s)", url, ref_desc)
        resp = self.session.post(url, json=body, timeout=(10, 120))
        logger.info("[Dzine] image_to_image response: status=%s", resp.status_code)
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
            logger.error("[Dzine] image_to_image non-JSON response: %s", resp.text[:500])
        logger.debug("[Dzine] image_to_image raw response: %s", data)
        data["_status_code"] = resp.status_code

        dzine_code = data.get("code")
        if resp.status_code >= 400 or (dzine_code is not None and int(dzine_code) != 200):
            logger.error("[Dzine] image_to_image FAILED: http=%s dzine_code=%s msg=%s", resp.status_code, dzine_code, data.get("msg") or data.get("detail") or data)
        else:
            logger.info("[Dzine] image_to_image OK: task_id=%s", data.get("data", {}).get("task_id") or data.get("task_id"))
        return data

    def poll_task(
        self,
        task_id: str,
        max_wait: int = 300,
        interval: int = 5,
    ) -> Dict[str, Any]:
        """
        Poll a Dzine task until completion.
        Dzine tasks return a task_id; we poll their status endpoint.
        """
        url = f"{self.base_url}/get_task_progress/{task_id}"
        logger.info("[Dzine] poll_task starting: task_id=%s url=%s", task_id, url)
        start = time.time()
        last: Dict[str, Any] = {}

        while time.time() - start < max_wait:
            try:
                resp = self.session.get(url, timeout=(10, 30))
                try:
                    data = resp.json()
                except Exception:
                    data = {"error": resp.text}
                data["_status_code"] = resp.status_code
                last = data

                status = str(data.get("status") or data.get("data", {}).get("status") or "").lower()
                elapsed = int(time.time() - start)
                logger.info("[Dzine] poll_task %s: status=%s elapsed=%ds http=%s", task_id, status or "unknown", elapsed, resp.status_code)

                if resp.status_code >= 400:
                    logger.error("[Dzine] poll_task HTTP error: %s %s", resp.status_code, data.get("error") or data)

                if status in {"failed", "error"}:
                    logger.error("[Dzine] poll_task FAILED: %s", data)
                    return data
                if status in {"completed", "succeeded", "finished", "done", "success"}:
                    logger.info("[Dzine] poll_task COMPLETED: %s", task_id)
                    return data

                images = self._extract_images(data)
                if images:
                    data["_images"] = images
                    return data

            except requests.RequestException as e:
                last = {"error": f"request_error: {e}", "_status_code": 0}

            time.sleep(interval)

        return last or {"error": "Dzine task timed out", "status": "timeout"}

    def generate_image(
        self,
        prompt: str,
        seed: Optional[int] = None,
        width: int = 1024,
        height: int = 1024,
        reference_image_url: Optional[str] = None,
        reference_image_bytes: Optional[bytes] = None,
        image_format: str = "png",
        style_code: Optional[str] = None,
        structure_match: Optional[float] = None,
        color_match: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        High-level helper: generate an image (text-to-image or image-to-image),
        poll until complete, and return the result with image URLs.
        """
        if reference_image_url or reference_image_bytes:
            create_resp = self.image_to_image(
                prompt=prompt,
                reference_image_url=reference_image_url,
                reference_image_bytes=reference_image_bytes,
                image_format=image_format,
                seed=seed,
                style_code=style_code,
                structure_match=structure_match,
                color_match=color_match,
            )
        else:
            create_resp = self.text_to_image(
                prompt=prompt, seed=seed, width=width, height=height,
                style_code=style_code,
            )

        http_code = int(create_resp.get("_status_code", 0))
        dzine_code = create_resp.get("code")
        is_error = http_code >= 400 or (dzine_code is not None and int(dzine_code) != 200)

        if is_error:
            logger.error("[Dzine] generate_image creation failed: %s", create_resp)
            return {"success": False, "error": create_resp}

        task_id = (
            create_resp.get("task_id")
            or create_resp.get("data", {}).get("task_id")
            or create_resp.get("id")
        )
        logger.info("[Dzine] generate_image extracted task_id=%s", task_id)
        if not task_id:
            images = self._extract_images(create_resp)
            if images:
                return {"success": True, "images": images, "raw": create_resp}
            return {"success": False, "error": "No task_id in response", "raw": create_resp}

        poll_result = self.poll_task(task_id)
        images = poll_result.get("_images") or self._extract_images(poll_result)
        if images:
            return {"success": True, "images": images, "task_id": task_id, "raw": poll_result}
        return {"success": False, "error": poll_result, "task_id": task_id}

    def _extract_images(self, data: Dict[str, Any]) -> List[str]:
        """Extract image URLs from Dzine response data."""
        urls: List[str] = []

        def _walk(obj: Any) -> None:
            if isinstance(obj, str) and obj.startswith("http"):
                lower = obj.lower()
                if any(lower.endswith(ext) or f"{ext}?" in lower for ext in (".png", ".jpg", ".jpeg", ".webp")):
                    urls.append(obj)
            elif isinstance(obj, dict):
                for v in obj.values():
                    _walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    _walk(item)

        _walk(data)
        return urls

    def download_image(self, url: str) -> bytes:
        """Download an image from a URL and return raw bytes."""
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
