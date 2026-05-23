import logging
import time
from typing import Any, Dict, Optional

import jwt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)

MOTION_CONTROL_PATH = "/v1/videos/motion-control"

# JWT lifetime per Kling docs: 30 minutes; nbf backdated 5s for clock skew
_JWT_TTL_SECONDS = 1800
_JWT_NBF_OFFSET = 5

# Per Kling error code table (debug/Error_Code_*):
#   1xxx auth/account/params/policy — NOT retryable
#   5xxx server internal — retryable with backoff
_RETRYABLE_STATUS = (502, 503, 504)


class KlingMotionClient:
    """Direct client for Kling Motion Control API.

    Auth: HS256 JWT regenerated per request from access_key (iss) signed by secret_key.
    Endpoint base: KLING_API_BASE_URL (default https://api-singapore.klingai.com).

    Model-version trade-off (S72):
      Default `model_name` is "kling-v3" (Kling 3.0), bumped from "kling-v2-6".
      v3 wins: better facial consistency, longer cap (30s for video-orientation
      vs v2.6's same cap but weaker face transfer).
      v3 cost: ~2× v2.6 at the Kling-API level — measured S72 Thriller spike at
      v3 std+video+15s = ~$2.00 Kling-side, vs v2.6 pro+image+10s = ~$1.02
      (per docs/V2_motion_transfer_plan.md:44 historical COGS).
      Revert path: if v3's quality lift doesn't justify the 2× cost on real
      user usage data, flip the default back to "kling-v2-6" — single-line
      change at lines 72 + 148. v2.6 is the cheaper option we want to keep
      available.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.access_key = self.settings.kling_access_key
        self.secret_key = self.settings.kling_secret_key
        self.base_url = self.settings.kling_api_base_url.rstrip("/")

        self.session = requests.Session()
        # Retries on polling GET only — POST submit must not auto-retry
        # (could double-charge or collide with content-moderation rejection).
        get_retry = Retry(
            total=3, connect=3, read=3,
            backoff_factor=0.8,
            status_forcelist=_RETRYABLE_STATUS,
            allowed_methods=("GET",),
            raise_on_status=False,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=get_retry))

    def _make_jwt(self) -> str:
        now = int(time.time())
        payload = {
            "iss": self.access_key,
            "exp": now + _JWT_TTL_SECONDS,
            "nbf": now - _JWT_NBF_OFFSET,
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._make_jwt()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def submit(
        self,
        image_url: str,
        video_url: str,
        character_orientation: str,
        mode: str = "pro",
        model_name: str = "kling-v3",  # S72: flipped from "kling-v2-6" for facial consistency (Kling 3.0). Revert if v3 quality regresses on our flow.
        prompt: Optional[str] = None,
        keep_original_sound: str = "yes",
        watermark_enabled: bool = False,
        callback_url: Optional[str] = None,
        external_task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a motion-control task.

        character_orientation selects character pose-orientation source, NOT scene
        source. Per S58 empirical, BOTH modes produce Outcome 2 (motion-onto-character)
        on their own — the input image's background wins in both cases.
          - "image" → pose orientation from reference image; driving video ≤10s.
            Pipeline A flow (NBP cosmetic edit → this client → animated output).
          - "video" → pose orientation from driving video; driving video ≤30s.
            Pipeline B uses this as its I2V step AFTER NBP has already composited
            the character into the target scene. This mode does NOT do scene
            composition on its own — Pipeline B's Outcome-1 result comes from the
            NBP pre-step.

        Returns the parsed JSON response with `_status_code` injected.
        """
        url = f"{self.base_url}{MOTION_CONTROL_PATH}"
        body: Dict[str, Any] = {
            "model_name": model_name,
            "image_url": image_url,
            "video_url": video_url,
            "character_orientation": character_orientation,
            "mode": mode,
            "keep_original_sound": keep_original_sound,
            "watermark_info": {"enabled": watermark_enabled},
        }
        if prompt:
            body["prompt"] = prompt
        if callback_url:
            body["callback_url"] = callback_url
        if external_task_id:
            body["external_task_id"] = external_task_id

        logger.info(
            "[Kling] submit POST %s model=%s orientation=%s mode=%s",
            url, model_name, character_orientation, mode,
        )
        try:
            resp = self.session.post(url, json=body, headers=self._headers(), timeout=(10, 45))
            data = resp.json()
            data["_status_code"] = resp.status_code
            logger.info("[Kling] submit response: status=%s code=%s message=%s",
                        resp.status_code, data.get("code"), data.get("message"))
            return data
        except requests.Timeout as e:
            logger.error("[Kling] submit timeout: %s", e)
            return {"error": f"timeout: {e}", "_status_code": 0}
        except requests.RequestException as e:
            logger.error("[Kling] submit request error: %s", e)
            return {"error": f"request_error: {e}", "_status_code": 0}

    def poll(self, task_id: str) -> Dict[str, Any]:
        """Query single task status. Returns parsed JSON with `_status_code` injected."""
        url = f"{self.base_url}{MOTION_CONTROL_PATH}/{task_id}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=(10, 30))
            data = resp.json()
            data["_status_code"] = resp.status_code
            return data
        except requests.Timeout as e:
            return {"error": f"timeout: {e}", "_status_code": 0}
        except requests.RequestException as e:
            return {"error": f"request_error: {e}", "_status_code": 0}

    def generate_and_poll(
        self,
        image_url: str,
        video_url: str,
        character_orientation: str,
        mode: str = "pro",
        model_name: str = "kling-v3",  # S72: flipped from "kling-v2-6". Revert if v3 regresses.
        prompt: Optional[str] = None,
        keep_original_sound: str = "yes",
        max_wait: int = 600,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """Submit + poll until completion.

        Returns:
            {"success": True, "video_url": "...", "task_id": "...", "duration": "..."}
            or {"success": False, "error": ..., "task_id": "..."} on failure/timeout.

        URL in the result expires 30 days after generation per Kling — caller is
        responsible for downloading and rehosting if longer retention is needed.
        """
        # Step 1: submit
        submit_data = self.submit(
            image_url=image_url,
            video_url=video_url,
            character_orientation=character_orientation,
            mode=mode,
            model_name=model_name,
            prompt=prompt,
            keep_original_sound=keep_original_sound,
        )
        status_code = int(submit_data.get("_status_code", 0))
        if not (200 <= status_code < 300) or submit_data.get("code") != 0:
            return {"success": False, "error": submit_data}

        task_id = (submit_data.get("data") or {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "No task_id in response", "raw": submit_data}

        logger.info("[Kling] task_id=%s — polling (max %ds)", task_id, max_wait)

        # Step 2: poll
        start = time.time()
        last_status: Dict[str, Any] = {}
        while time.time() - start < max_wait:
            last_status = self.poll(task_id)
            data = last_status.get("data") or {}
            task_status = str(data.get("task_status", "")).lower()
            logger.debug("[Kling] poll task_id=%s status=%s", task_id, task_status)

            if task_status == "failed":
                return {
                    "success": False,
                    "error": data.get("task_status_msg") or last_status,
                    "task_id": task_id,
                }
            if task_status == "succeed":
                videos = ((data.get("task_result") or {}).get("videos")) or []
                if not videos:
                    return {
                        "success": False,
                        "error": "Succeeded but no videos in result",
                        "raw": last_status,
                        "task_id": task_id,
                    }
                video = videos[0]
                video_url_out = video.get("url")
                if not video_url_out:
                    return {
                        "success": False,
                        "error": "Video entry missing url",
                        "raw": last_status,
                        "task_id": task_id,
                    }
                logger.info("[Kling] video ready: task_id=%s duration=%s",
                            task_id, video.get("duration"))
                return {
                    "success": True,
                    "video_url": video_url_out,
                    "task_id": task_id,
                    "duration": video.get("duration"),
                    "video_id": video.get("id"),
                }

            # submitted | processing → keep polling
            time.sleep(poll_interval)

        return {
            "success": False,
            "error": "Generation timed out",
            "task_id": task_id,
            "last_status": last_status,
        }
