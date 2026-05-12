"""Vertex AI client for Nano Banana Pro (T2I + Edit) — V2 Pipeline B (AIV-11).

Auth precedence: VERTEX_SERVICE_ACCOUNT_JSON → VERTEX_SERVICE_ACCOUNT_PATH.
Lazy `genai.Client(vertexai=True, project, location, credentials)` — one client per
instance, scoped to the configured project + region.

Returns local file paths, NOT URLs. The dispatcher (AIV-14) handles R2 upload /
presign / pass-through. Keeps this client decoupled from blob storage.

Quotas: `gemini-2.5-flash-image-preview` is preview-tier on new projects. First
403 quota error → manual GCP Console → IAM → Quotas → search "aiplatform" →
request increase.
"""
from __future__ import annotations

import json
import logging
import mimetypes
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Sequence

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


class VertexAIClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        from google import genai
        from google.oauth2 import service_account

        s = self.settings
        if not s.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set")

        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        if s.vertex_service_account_json:
            info = json.loads(s.vertex_service_account_json)
            creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        elif s.vertex_service_account_path:
            path = os.path.expanduser(s.vertex_service_account_path)
            creds = service_account.Credentials.from_service_account_file(path, scopes=scopes)
        else:
            raise RuntimeError(
                "VERTEX_SERVICE_ACCOUNT_JSON or VERTEX_SERVICE_ACCOUNT_PATH must be set"
            )

        self._client = genai.Client(
            vertexai=True,
            project=s.google_cloud_project,
            location=s.vertex_location,
            credentials=creds,
        )
        logger.info(
            "[Vertex] genai.Client(vertexai=True) ready: project=%s location=%s",
            s.google_cloud_project, s.vertex_location,
        )
        return self._client

    def generate_image_nano_banana(
        self,
        prompt: str,
        output_dir: str = "/tmp",
    ) -> Dict[str, Any]:
        """T2I via Nano Banana Pro. Returns {success, local_path, model, mime_type}
        on success; {success: False, error} on failure."""
        return self._generate_image(prompt, image_paths=None, output_dir=output_dir, op_label="T2I")

    def edit_image_nano_banana(
        self,
        prompt: str,
        image_paths: Sequence[str],
        output_dir: str = "/tmp",
    ) -> Dict[str, Any]:
        """Edit via Nano Banana Pro. `image_paths` = list of local file paths
        (e.g., [user_selfie, scene_image]). Returns {success, local_path, model,
        mime_type} on success; {success: False, error} on failure."""
        return self._generate_image(
            prompt, image_paths=list(image_paths), output_dir=output_dir, op_label="Edit",
        )

    def _generate_image(
        self,
        prompt: str,
        image_paths: Optional[List[str]],
        output_dir: str,
        op_label: str,
    ) -> Dict[str, Any]:
        from google.genai import types

        model = self.settings.vertex_nb_model
        client = self._get_client()

        contents: List[Any] = [prompt]
        if image_paths:
            for p in image_paths:
                if not os.path.exists(p):
                    return {"success": False, "error": f"image not found: {p}"}
                mime = mimetypes.guess_type(p)[0] or "image/png"
                with open(p, "rb") as f:
                    contents.append(types.Part.from_bytes(data=f.read(), mime_type=mime))

        logger.info(
            "[Vertex] %s submit model=%s prompt=%r images=%d",
            op_label, model, prompt[:80], len(image_paths) if image_paths else 0,
        )

        try:
            t0 = time.time()
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
            logger.info("[Vertex] %s ok in %.1fs", op_label, time.time() - t0)
        except Exception as e:
            logger.error("[Vertex] %s failed: %s", op_label, e)
            return {"success": False, "error": f"{type(e).__name__}: {e}"}

        image_bytes = None
        out_mime = "image/png"
        for cand in resp.candidates or []:
            content = getattr(cand, "content", None)
            if content is None:
                continue
            for part in content.parts or []:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    image_bytes = inline.data
                    if getattr(inline, "mime_type", None):
                        out_mime = inline.mime_type
                    break
            if image_bytes:
                break

        if not image_bytes:
            return {"success": False, "error": "no image in response", "raw": str(resp)[:500]}

        ext = "png" if "png" in out_mime else ("jpg" if "jpeg" in out_mime else "bin")
        os.makedirs(output_dir, exist_ok=True)
        prefix = "nb_edit" if image_paths else "nb_t2i"
        path = os.path.join(output_dir, f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}")
        with open(path, "wb") as f:
            f.write(image_bytes)
        logger.info("[Vertex] %s saved %s (%d bytes)", op_label, path, len(image_bytes))

        return {"success": True, "local_path": path, "model": model, "mime_type": out_mime}
