"""Google AI Studio direct client for Nano Banana Pro / Gemini image models.

S66: introduced for the Pipeline A NBP regen step. Will subsume the bulk of
`vertex_ai_client.py` over time per AIV-91. For now exposes only what
Pipeline A needs (single-input image regen via the Edit pathway).

Auth: `NBP_API_Key` (paid-tier AI Studio key, no allowlist). Model defaults to
`gemini-3-pro-image-preview` — same model the Vertex client was hitting via
the allowlisted path, just over the AI Studio surface.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Minimal AI Studio direct client. Lazy SDK init; no boto/genai imports at
    module-load time so test/CLI paths that never touch image gen aren't taxed."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        if not self.settings.nbp_api_key:
            raise RuntimeError(
                "NBP_API_Key not configured — set it in .env / deployment secrets"
            )
        self.model = self.settings.nbp_model
        self._client = None

    def _genai(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.settings.nbp_api_key)
        return self._client

    def regen_image(self, image_bytes: bytes, mime: str, prompt: str) -> Dict[str, Any]:
        """Edit-mode single-input regen.

        Returns:
            {"success": True, "image_bytes": bytes, "mime": str}
            or {"success": False, "error": str} on failure / no-image response.
        """
        from google.genai import types

        logger.info("[Gemini] regen submit  model=%s  prompt=%r", self.model, prompt[:120])
        try:
            resp = self._genai().models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime),
                    prompt,
                ],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
        except Exception as e:
            logger.error("[Gemini] regen exception: %s: %s", type(e).__name__, e)
            return {"success": False, "error": f"{type(e).__name__}: {e}"}

        for cand in resp.candidates or []:
            content = getattr(cand, "content", None)
            if content is None:
                continue
            for part in content.parts or []:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    out_mime = getattr(inline, "mime_type", None) or "image/png"
                    logger.info("[Gemini] regen ok  mime=%s  bytes=%d", out_mime, len(inline.data))
                    return {"success": True, "image_bytes": inline.data, "mime": out_mime}

        logger.error("[Gemini] regen returned no image part")
        return {"success": False, "error": "no image part in response"}
