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

    def generate_scene_bible_and_stages(
        self,
        room_type: str,
        style: str,
        features: List[str],
        materials: List[str],
        lighting: str,
        camera_motion: str,
        progression: str,
        num_stages: int = 7,
        freeform: str = "",
    ) -> Dict[str, object]:
        """
        Generate a Scene Bible (constant base description) and N stage deltas
        for a multi-step interior timelapse pipeline.

        Returns {"scene_bible": str, "stages": [{"stage": int, "description": str, "transition_prompt": str}]}
        """
        features_str = ", ".join(features) if features else "standard fixtures"
        materials_str = ", ".join(materials) if materials else "appropriate materials"
        freeform_clause = f"\nAdditional direction: {freeform}" if freeform.strip() else ""

        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert architectural visualization director planning a multi-stage "
                        "construction timelapse for interior design.\n\n"
                        "You will produce TWO things:\n\n"
                        "1. A SCENE BIBLE (MAX 400 CHARACTERS): A dense, comma-separated list of constants that "
                        "NEVER change across stages: camera position/lens, room shape, perspective, light "
                        "direction, color temp, render style. Be terse—use shorthand, no full sentences. "
                        "Example: '24mm eye-level centered, straight-run stairwell, soft daylight from above, "
                        "5200K cool-neutral, ultra-photorealistic arch-viz, no DOF, no color grading.'\n\n"
                        f"2. EXACTLY {num_stages} STAGE DELTAS (MAX 200 CHARACTERS EACH): Each stage describes "
                        "ONLY what changes. Be concise—list materials and actions, skip flowery language. "
                        "Stage 1 is always the empty starting space. The final stage is the polished result "
                        "with no crew/tools/dust.\n\n"
                        "For each stage, also write a TRANSITION PROMPT (MAX 150 CHARACTERS) describing how "
                        "the scene visually TRANSFORMS from this stage to the next. Focus on material changes "
                        "and visual morphing (e.g., 'walls fade from bare concrete to smooth white paint, "
                        "wood grain materializes on treads'). NEVER mention people, crews, workers, hands, "
                        "or tools—describe only the environment changing. The last stage has no transition.\n\n"
                        "CHARACTER LIMITS ARE STRICT. The scene bible + any single stage description must total "
                        "under 700 characters combined. Trim aggressively.\n\n"
                        "Respond in EXACTLY this format:\n"
                        "SCENE_BIBLE: [paragraph]\n"
                        "STAGE_1: [description]\n"
                        "TRANSITION_1: [motion description]\n"
                        "STAGE_2: [description]\n"
                        "TRANSITION_2: [motion description]\n"
                        "...\n"
                        f"STAGE_{num_stages}: [description]\n"
                        "TRANSITION_FINAL: none"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Room type: {room_type}\n"
                        f"Style: {style}\n"
                        f"Key features: {features_str}\n"
                        f"Materials: {materials_str}\n"
                        f"Lighting: {lighting}\n"
                        f"Camera: {camera_motion}\n"
                        f"Progression type: {progression}"
                        f"{freeform_clause}"
                    ),
                },
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""

        scene_bible = ""
        stages: List[Dict[str, object]] = []
        current_stage_desc = ""
        current_stage_num = 0
        transitions: Dict[int, str] = {}

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            upper = line.upper()
            if upper.startswith("SCENE_BIBLE:"):
                scene_bible = line[len("SCENE_BIBLE:"):].strip()
            elif upper.startswith("STAGE_"):
                if current_stage_num > 0 and current_stage_desc:
                    stages.append({
                        "stage": current_stage_num,
                        "description": current_stage_desc,
                    })
                try:
                    parts = upper.split(":", 1)
                    current_stage_num = int(parts[0].replace("STAGE_", "").strip())
                    current_stage_desc = line.split(":", 1)[1].strip() if ":" in line else ""
                except (ValueError, IndexError):
                    current_stage_desc = line
            elif upper.startswith("TRANSITION_"):
                try:
                    parts = upper.split(":", 1)
                    t_key = parts[0].replace("TRANSITION_", "").strip()
                    t_val = line.split(":", 1)[1].strip() if ":" in line else ""
                    if t_key.lower() != "final" and t_val.lower() != "none":
                        transitions[int(t_key)] = t_val
                except (ValueError, IndexError):
                    pass

        if current_stage_num > 0 and current_stage_desc:
            stages.append({
                "stage": current_stage_num,
                "description": current_stage_desc,
            })

        for s in stages:
            s_num = int(s["stage"])
            s["transition_prompt"] = transitions.get(s_num, "")

        if not scene_bible:
            scene_bible = (
                f"Ultra photorealistic {style} {room_type}, locked camera, 24mm lens, "
                f"eye-level centered composition, {lighting} lighting, high-end architectural visualization."
            )

        if not stages:
            stages = [
                {"stage": 1, "description": f"Empty {room_type}, bare structure, no furnishings.", "transition_prompt": "Construction crew arrives with tools and materials."},
                {"stage": 2, "description": f"Structural framework being installed.", "transition_prompt": "Workers fitting primary surfaces."},
                {"stage": 3, "description": f"{features_str} being installed with {materials_str}.", "transition_prompt": "Final finishes being applied."},
                {"stage": 4, "description": f"Completed {style} {room_type}, all construction removed, polished.", "transition_prompt": ""},
            ]

        return {"scene_bible": scene_bible, "stages": stages}

    def create_timelapse_progression(self, base_prompt: str, total_duration: int) -> List[Dict[str, object]]:
        """
        Break an interior design timelapse prompt into sequential construction phases
        rather than narrative story beats.
        """
        num_scenes = max(1, total_duration // 10)
        if num_scenes <= 1:
            return [{"prompt": base_prompt, "duration": total_duration}]

        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an architectural visualization director. Break this interior design "
                        f"timelapse concept into EXACTLY {num_scenes} sequential construction phases.\n\n"
                        "Rules:\n"
                        "1. Each phase shows a distinct stage of building/installing the space\n"
                        "2. Progress through: empty shell/structure -> framework/rough construction -> "
                        "material installation -> feature additions -> lighting and finishing -> "
                        "final cinematic reveal\n"
                        "3. Every phase MUST maintain the exact same room geometry, camera angle, "
                        "and architectural style\n"
                        "4. Describe what the camera SEES in each phase, not abstract concepts\n"
                        "5. Each phase description should be a single detailed sentence\n\n"
                        f"Respond with EXACTLY {num_scenes} lines, one per phase. "
                        "No numbering, no bullets, no extra text."
                    ),
                },
                {"role": "user", "content": f"Timelapse concept: {base_prompt}"},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        # Strip any leading numbering like "1." or "- "
        cleaned: List[str] = []
        for line in lines:
            stripped = line.lstrip("0123456789.-) ").strip()
            if stripped:
                cleaned.append(stripped)

        scenes: List[Dict[str, object]] = []
        for phase_desc in cleaned[:num_scenes]:
            scenes.append({
                "prompt": f"{base_prompt} Current phase: {phase_desc}",
                "duration": 10,
            })

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


