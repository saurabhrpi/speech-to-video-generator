import io
import os
import time
from typing import Dict, List, Optional

from openai import OpenAI

from ..utils.config import Settings, get_settings


class OpenAIClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            organization=self.settings.openai_org_id or None,
            project=self.settings.openai_project or None,
        )

    def transcribe(self, audio_path: str) -> Dict[str, str]:
        """
        Transcribe speech audio using Whisper model.
        Uses an in-memory stream and retries to mitigate h11 Content-Length issues.
        Returns a dict with key "text".
        """
        with open(audio_path, "rb") as f:
            data = f.read()

        # Prepare an in-memory stream with a filename to help multipart form encoding
        def _make_stream() -> io.BytesIO:
            bio = io.BytesIO(data)
            # Provide a name attribute so the SDK sets a filename in multipart
            bio.name = os.path.basename(audio_path) or "audio.wav"
            return bio

        backoff_seconds = 1.0
        last_err: Optional[Exception] = None
        for _ in range(3):
            try:
                transcript = self.client.audio.transcriptions.create(
                    model=self.settings.openai_transcribe_model,
                    file=_make_stream(),
                )
                text = getattr(transcript, "text", None)
                if text is None and isinstance(transcript, dict):
                    text = transcript.get("text")
                return {"text": text or ""}
            except Exception as exc:  # transient network/protocol retries
                message = str(exc)
                if (
                    "Content-Length" in message
                    or "LocalProtocolError" in message
                    or "RemoteProtocolError" in message
                    or "Connection reset" in message
                ):
                    last_err = exc
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2.0
                    continue
                raise

        # If we exhausted retries, raise the last error to surface details upstream
        if last_err:
            raise last_err
        return {"text": ""}

    def create_scene_progression(self, base_prompt: str, total_duration: int) -> List[Dict[str, object]]:
        """
        Ask Chat Completions API to propose a coherent scene breakdown.
        """
        num_scenes = max(1, total_duration // 10)
        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Break this video concept into {num_scenes} sequential scenes that tell a coherent "
                        "story. Each scene should flow naturally into the next and maintain visual consistency."
                    ),
                },
                {"role": "user", "content": f"Base concept: {base_prompt}"},
            ],
        )

        content = response.choices[0].message.content or ""
        lines = [line.strip().lstrip("- ") for line in content.split("\n") if line.strip()]

        scenes: List[Dict[str, object]] = []
        for line in lines:
            scenes.append({"prompt": f"{base_prompt}. {line}", "duration": 10})

        if not scenes:
            scenes.append({"prompt": base_prompt, "duration": total_duration})

        return scenes


