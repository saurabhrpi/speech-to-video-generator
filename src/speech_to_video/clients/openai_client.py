import io
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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
                        "renovation timelapse for ONE SINGLE ROOM.\n\n"
                        "CRITICAL RULE: All stages depict the SAME PHYSICAL ROOM. The room's shape, "
                        "dimensions, windows, doors, and architectural bones NEVER change—only surfaces, "
                        "finishes, fixtures, and furnishings evolve.\n\n"
                        "You will produce THREE things:\n\n"
                        "1. A SCENE BIBLE (MAX 400 CHARACTERS): A dense, comma-separated list of constants that "
                        "NEVER change across stages: camera position/lens, room shape & dimensions, architectural "
                        "bones (walls, ceiling, floor footprint, window/door positions), perspective, light "
                        "direction, color temp, render style. Be terse—use shorthand, no full sentences. "
                        "Example: '24mm eye-level centered, 4m x 6m rectangular room, single window left wall, "
                        "door rear-right, 2.8m ceiling, soft daylight from left, 5200K cool-neutral, "
                        "ultra-photorealistic arch-viz, no DOF.'\n\n"
                        "2. STAGE 1 DESCRIPTION (MAX 300 CHARACTERS): The COMPLETE visible state of the "
                        "bare/unfinished starting room. Include all surfaces, materials, and fixtures present. "
                        "This is used to generate the first image from scratch.\n\n"
                        f"3. EDIT INSTRUCTIONS FOR STAGES 2-{num_stages} (MAX 250 CHARACTERS EACH): "
                        "For each subsequent stage, write SPECIFIC EDIT INSTRUCTIONS describing what to "
                        "CHANGE, ADD, or REMOVE relative to the previous stage's image. These edits will be "
                        "applied to the previous image, so be precise: name the elements being modified and "
                        "their new state. Do NOT repeat unchanged elements. "
                        "Example: 'Change bare concrete walls to smooth white paint. Replace exposed wiring "
                        "with recessed LED strips. Add polished oak treads over raw plywood steps.'\n\n"
                        "NEVER mention people, crews, workers, hands, or tools in ANY output.\n\n"
                        "For each stage, also write a TRANSITION PROMPT (MAX 150 CHARACTERS) describing how "
                        "the scene visually TRANSFORMS from this stage to the next. Focus on material changes "
                        "and visual morphing. The last stage has no transition.\n\n"
                        "CHARACTER LIMITS ARE STRICT. Trim aggressively.\n\n"
                        "Respond in EXACTLY this format:\n"
                        "SCENE_BIBLE: [paragraph]\n"
                        "STAGE_1: [complete room state description]\n"
                        "TRANSITION_1: [visual morphing description]\n"
                        "EDIT_2: [what to change/add/remove from stage 1 image]\n"
                        "TRANSITION_2: [visual morphing description]\n"
                        "EDIT_3: [what to change/add/remove from stage 2 image]\n"
                        "TRANSITION_3: [visual morphing description]\n"
                        "...\n"
                        f"EDIT_{num_stages}: [what to change/add/remove from stage {num_stages - 1} image]\n"
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
        transitions: Dict[int, str] = {}
        edit_deltas: Dict[int, str] = {}
        stage_1_desc = ""

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            upper = line.upper()
            if upper.startswith("SCENE_BIBLE:"):
                scene_bible = line[len("SCENE_BIBLE:"):].strip()
            elif upper.startswith("STAGE_1:") or upper.startswith("STAGE_1 :"):
                stage_1_desc = line.split(":", 1)[1].strip() if ":" in line else ""
            elif upper.startswith("EDIT_"):
                try:
                    parts = upper.split(":", 1)
                    e_num = int(parts[0].replace("EDIT_", "").strip())
                    e_val = line.split(":", 1)[1].strip() if ":" in line else ""
                    edit_deltas[e_num] = e_val
                except (ValueError, IndexError):
                    pass
            elif upper.startswith("STAGE_"):
                try:
                    parts = upper.split(":", 1)
                    s_num = int(parts[0].replace("STAGE_", "").strip())
                    s_val = line.split(":", 1)[1].strip() if ":" in line else ""
                    edit_deltas[s_num] = s_val
                except (ValueError, IndexError):
                    pass
            elif upper.startswith("TRANSITION_"):
                try:
                    parts = upper.split(":", 1)
                    t_key = parts[0].replace("TRANSITION_", "").strip()
                    t_val = line.split(":", 1)[1].strip() if ":" in line else ""
                    if t_key.lower() != "final" and t_val.lower() != "none":
                        transitions[int(t_key)] = t_val
                except (ValueError, IndexError):
                    pass

        if stage_1_desc:
            stages.append({
                "stage": 1,
                "description": stage_1_desc,
                "edit_delta": "",
            })

        for s_num in sorted(edit_deltas.keys()):
            stages.append({
                "stage": s_num,
                "description": edit_deltas[s_num],
                "edit_delta": edit_deltas[s_num],
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

    def generate_scene_bible_only(
        self,
        room_type: str,
        style: str,
        features: List[str],
        materials: List[str],
        lighting: str,
        camera_motion: str,
        progression: str,
        freeform: str = "",
    ) -> Dict[str, Any]:
        features_str = ", ".join(features) if features else "standard fixtures"
        materials_str = ", ".join(materials) if materials else "appropriate materials"
        freeform_clause = f"\nAdditional direction: {freeform}" if freeform.strip() else ""

        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert architectural visualization director.\n\n"
                        "Produce THREE things for a room renovation timelapse:\n\n"
                        "1. SCENE BIBLE (MAX 300 chars): Camera position/lens, room shape & "
                        "dimensions, architectural bones (walls, ceiling, floor, windows, doors), "
                        "perspective, light direction, render style. Terse comma-separated shorthand.\n\n"
                        "2. ELEMENTS: List the HIGH-LEVEL visual element groups in this room as a "
                        "comma-separated list. EXACTLY 5 to 7 items. Group related sub-parts into "
                        "ONE element. Use GENERIC FUNCTIONAL CATEGORY names — the element name "
                        "describes the SLOT in the room, not the specific fixture that fills it.\n"
                        "GOOD: floor, walls, ceiling, window, door, lighting, cabinetry\n"
                        "BAD: chandelier, pendant, sconce (use 'lighting').\n"
                        "BAD: hardwood, tile, carpet (use 'floor').\n"
                        "BAD: window frame, window sash (use 'window').\n"
                        "BAD: Wall A drywall, Wall B drywall (use 'walls').\n"
                        "Each element must be a single word or two-word generic label. "
                        "NO specific fixture types, NO materials, NO sub-components. "
                        "STRICTLY 5-7 items.\n\n"
                        "3. STAGE 1 DESCRIPTION (MAX 200 chars): The current visible state of the "
                        "room BEFORE any renovation. The room is EMPTY — NO loose items, NO "
                        "clutter, NO boxes, NO newspapers, NO debris on the floor. Describe "
                        "only surface-level wear: scuffs, stains, cracks, patchy paint, dated "
                        "fixtures. NO people. Be specific and visual.\n\n"
                        "Respond in EXACTLY this format:\n"
                        "SCENE_BIBLE: [text]\n"
                        "ELEMENTS: [comma-separated list]\n"
                        "STAGE_1: [text]"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Room: {room_type}\nStyle goal: {style}\n"
                        f"Features: {features_str}\nMaterials: {materials_str}\n"
                        f"Lighting: {lighting}\nCamera: {camera_motion}\n"
                        f"Progression: {progression}{freeform_clause}"
                    ),
                },
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""
        scene_bible = ""
        elements = ""
        stage_1_desc = ""
        for line in content.split("\n"):
            line = line.strip()
            upper = line.upper()
            if upper.startswith("SCENE_BIBLE:"):
                scene_bible = line[len("SCENE_BIBLE:"):].strip()
            elif upper.startswith("ELEMENTS:"):
                elements = line[len("ELEMENTS:"):].strip()
            elif upper.startswith("STAGE_1:"):
                stage_1_desc = line[len("STAGE_1:"):].strip()

        if not scene_bible:
            scene_bible = (
                f"Ultra photorealistic {style} {room_type}, locked camera, 24mm lens, "
                f"eye-level centered, {lighting} lighting, arch-viz."
            )
        if not elements:
            elements = "floor, left wall, right wall, back wall, ceiling, window, door frame, light fixtures"
        if not stage_1_desc:
            stage_1_desc = f"Dilapidated {room_type}, bare walls, exposed wiring, damaged surfaces."

        elements_list = [e.strip() for e in elements.split(",") if e.strip()]

        return {
            "scene_bible": scene_bible,
            "stage_1_description": stage_1_desc,
            "elements": elements_list,
        }

    def generate_next_stage(
        self,
        scene_bible: str,
        prev_description: str,
        prev_image_url: str,
        stage_num: int,
        total_stages: int,
        all_elements: List[str],
        renovated_elements: List[str],
        room_state: str = "",
        grouping_hint: str = "",
    ) -> Dict[str, Any]:
        remaining = [e for e in all_elements if e not in renovated_elements]
        remaining_str = ", ".join(remaining) if remaining else "none"
        renovated_str = ", ".join(renovated_elements) if renovated_elements else "none yet"
        stages_left = total_stages - stage_num

        task_focus = (
            "RENOVATION: ADD or UPGRADE one element — install new materials, new "
            "surfaces, new fixtures. The change must be VISUALLY DRAMATIC — a full "
            "surface or material transformation visible at room scale.\n"
            "ORDERING RULE: Renovate SURFACE changes first (floor, walls, ceiling, "
            "window, door, lighting), then ADDITIONS last (built-ins, cabinetry, "
            "shelving, accent features — anything not currently in the image).\n"
            "ADDITION RULE: If an element is an ADDITION (not currently visible in "
            "the room), spread it across 2 stages: first the structure/frame, then "
            "the finishing/details."
        )
        if grouping_hint:
            task_focus += f"\n{grouping_hint}"

        if stages_left <= 0 and len(remaining) > 1:
            element_rule = (
                f"This is the LAST stage. Renovate ALL remaining elements "
                f"({remaining_str}) in this one stage."
            )
        elif len(remaining) > stages_left > 0:
            element_rule = (
                f"REMAINING: {remaining_str} ({len(remaining)} left, "
                f"{stages_left} stages after this). You may group 2 related "
                "surface elements to free up stages for additions."
            )
        else:
            element_rule = (
                f"REMAINING: {remaining_str}. "
                f"DONE: {renovated_str}. "
                "Pick EXACTLY ONE element to renovate."
            )

        room_state_block = ""
        if room_state:
            room_state_block = (
                f"CURRENT ROOM STATE (for your awareness of what has been done):\n"
                f"{room_state}\n\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an architectural renovation director. You will see an image of "
                    "a room and its text description. Plan the NEXT renovation step.\n\n"
                    "IMPORTANT: There are NO people, NO workers, NO humans in this timelapse. "
                    "Renovations happen as if by magic — surfaces transform, materials change, "
                    "fixtures upgrade. Never mention people, hands, tools, crews, or ladders.\n\n"
                    f"This is stage {stage_num} of {total_stages}. {task_focus}\n\n"
                    f"Scene constants: {scene_bible}\n\n"
                    f"{room_state_block}"
                    f"ELEMENT SELECTION: {element_rule}\n\n"
                    "PERMANENCE RULE: Every element visible in the image that is NOT being "
                    "changed in this stage MUST remain exactly as-is — same position, size, "
                    "and appearance. Do NOT remove, shrink, move, or alter anything that "
                    "isn't explicitly part of this stage's edit.\n\n"
                    "Produce FIVE things:\n"
                    "1. EDIT (MAX 250 chars): Narrative description of what changes in this "
                    "stage. Describe the transformation result, not any human action.\n"
                    "2. IMAGE_PROMPT (MAX 200 chars): A SHORT editing instruction for the "
                    "image model. Describe ONLY the element being changed — nothing else.\n"
                    "   Rules:\n"
                    "   - Describe ONLY the renovated element's new appearance. Be specific "
                    "about the FULL result — e.g. 'Entire floor covered in large pale "
                    "porcelain tiles with light grout.'\n"
                    "   - Do NOT mention ANY other element in the room. The image model "
                    "already has the previous image — unchanged elements are preserved "
                    "automatically.\n"
                    "   - End with 'Change nothing else.'\n"
                    "   - NO people, NO workers, NO tools, NO ladders.\n"
                    "   - Use PLAIN element names only: 'door', 'window', 'ceiling', "
                    "'floor', 'walls'. NO qualifiers like 'entry', 'accent', 'main', "
                    "'primary', 'rear'. The image model uses the existing image to "
                    "locate the element.\n"
                    "   - Never say 'full-height', 'floor-to-ceiling', or 'enlarged'. "
                    "For door/window/glazing, include 'same size opening'. "
                    "Only material/finish/hardware change.\n"
                    "   - For ADDITIONS (elements not currently in the image), you MUST "
                    "specify the exact placement — which wall, which area. The image "
                    "model cannot guess where to place something new.\n"
                    "3. ELEMENT: Which element(s) from the canonical list are being "
                    "renovated. Use EXACT names from the list.\n"
                    "4. MATERIAL (MAX 60 chars): Short material/appearance summary of the "
                    "renovated element AFTER this stage. Example: 'floor: pale porcelain tiles' "
                    "or 'walls: deep matte greige paint'.\n"
                    "5. PARTIAL: 'yes' if this is phase 1 of a 2-stage addition (the element "
                    "still needs finishing next stage). 'no' if the element is fully done.\n\n"
                    "Respond EXACTLY:\n"
                    "EDIT: [text]\n"
                    "IMAGE_PROMPT: [text]\n"
                    "ELEMENT: [element name(s)]\n"
                    "MATERIAL: [text]\n"
                    "PARTIAL: [yes/no]"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Previous stage description: {prev_description}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": prev_image_url},
                    },
                ],
            },
        ]

        response = self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=messages,
            temperature=0.7,
        )

        def _parse_response(content: str):
            ed, ip, el, mat, partial = "", "", "", "", ""
            for line in content.split("\n"):
                line = line.strip()
                upper = line.upper()
                if upper.startswith("EDIT:"):
                    ed = line[len("EDIT:"):].strip()
                elif upper.startswith("IMAGE_PROMPT:"):
                    ip = line[len("IMAGE_PROMPT:"):].strip()
                elif upper.startswith("ELEMENT:"):
                    el = line[len("ELEMENT:"):].strip()
                elif upper.startswith("MATERIAL:"):
                    mat = line[len("MATERIAL:"):].strip()
                elif upper.startswith("PARTIAL:"):
                    partial = line[len("PARTIAL:"):].strip()
            return ed, ip, el, mat, partial

        content = response.choices[0].message.content or ""
        edit_delta, image_prompt, element_done, material, partial_flag = _parse_response(content)

        if not image_prompt:
            backoff = 2.0
            for attempt in range(1, 4):
                logger.warning("[GPT] IMAGE_PROMPT missing (attempt %d), retrying in %.0fs...", attempt, backoff)
                time.sleep(backoff)
                try:
                    retry_resp = self.client.chat.completions.create(
                        model=self.settings.openai_chat_model,
                        messages=messages,
                        temperature=0.7,
                    )
                    retry_content = retry_resp.choices[0].message.content or ""
                    ed2, ip2, el2, mat2, par2 = _parse_response(retry_content)
                    if ip2:
                        logger.info("[GPT] IMAGE_PROMPT recovered on retry %d", attempt)
                        if not edit_delta and ed2:
                            edit_delta = ed2
                        image_prompt = ip2
                        if not element_done and el2:
                            element_done = el2
                        if not material and mat2:
                            material = mat2
                        if not partial_flag and par2:
                            partial_flag = par2
                        break
                except Exception as exc:
                    logger.warning("[GPT] Retry %d failed: %s", attempt, exc)
                backoff *= 2.0

        if not image_prompt:
            remaining_names = ", ".join(remaining[:2]) if remaining else "surfaces"
            image_prompt = (
                f"Room with freshly renovated {remaining_names}. "
                "Empty room, no people. Everything else unchanged."
            )
            logger.error("[GPT] IMAGE_PROMPT missing after all retries, using safe fallback: %s", image_prompt)

        if not edit_delta:
            edit_delta = "Renovation continues — surfaces and fixtures are upgraded."

        raw_elements = [e.strip() for e in element_done.split(",") if e.strip()] if element_done else []
        canonical_set = {e.lower() for e in all_elements}
        newly_renovated = [e for e in raw_elements if e.lower() in canonical_set and e.lower() != "none"]

        material_clean = material if material.lower() not in ("none", "") else ""
        is_partial = partial_flag.lower().strip() in ("yes", "true", "1")

        return {
            "edit_delta": edit_delta,
            "image_prompt": image_prompt,
            "renovated_element": newly_renovated,
            "material": material_clean,
            "is_partial": is_partial,
        }

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


