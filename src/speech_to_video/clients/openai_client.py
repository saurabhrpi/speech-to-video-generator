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

    def split_prompt_for_two_clips(self, prompt: str) -> Dict[str, str]:
        """
        Use GPT to intelligently split a prompt into two parts for seamless 2-clip video generation.
        Returns {"clip1": "...", "clip2": "..."} with detailed scene descriptions.
        """
        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a video director. Split the user's video concept into exactly TWO sequential scenes "
                        "for a seamless 16-second video (8 seconds each). "
                        "Requirements:\n"
                        "1. Find a NATURAL narrative break point - don't just split text arbitrarily\n"
                        "2. Scene 1 should contain the setup/beginning action and end at a transition moment\n"
                        "3. Scene 2 should continue seamlessly from that moment and conclude the story\n"
                        "4. Both scenes must describe the SAME characters, environment, lighting, and visual style\n"
                        "5. Be specific and visual - describe what the camera sees, not abstract concepts\n"
                        "6. Scene 2 should start with 'Continuing from the previous moment...' to ensure continuity\n\n"
                        "Respond in EXACTLY this format (no other text):\n"
                        "SCENE1: [detailed visual description for first 8 seconds]\n"
                        "SCENE2: [detailed visual description for next 8 seconds, continuing seamlessly]"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""
        
        # Parse the response
        clip1 = ""
        clip2 = ""
        
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SCENE1:"):
                clip1 = line[7:].strip()
            elif line.upper().startswith("SCENE2:"):
                clip2 = line[7:].strip()
        
        # Fallback if parsing fails - split the original prompt
        if not clip1 or not clip2:
            # Simple fallback: use the prompt for both with position hints
            clip1 = f"Beginning of the scene: {prompt}. Focus on the setup and initial action."
            clip2 = f"Continuing seamlessly: {prompt}. Focus on the continuation and conclusion."
        
        return {"clip1": clip1, "clip2": clip2}


