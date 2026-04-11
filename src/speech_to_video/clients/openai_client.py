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
                        "Produce FOUR things for a room renovation timelapse:\n\n"
                        "1. SCENE BIBLE (MAX 300 chars): Camera position/lens, room shape & "
                        "dimensions, architectural bones (walls, ceiling, floor, windows, doors), "
                        "perspective, light direction, render style. Terse comma-separated shorthand.\n\n"
                        "2. ELEMENTS: List the HIGH-LEVEL visual element groups in this room as a "
                        "comma-separated list. EXACTLY 5 to 7 items. Only include elements that "
                        "ALREADY EXIST in the space AND have a tangible, visible surface or "
                        "fixture that can be refinished, repainted, retiled, or replaced. "
                        "Do not list architectural voids — open air, gaps, or empty spans "
                        "have no surface to renovate. Do not invent structural elements that "
                        "would change the fundamental nature of the room (e.g., do not add a "
                        "ceiling to an open-air space, do not add walls to an open pavilion). "
                        "Group related sub-parts into ONE element. Use GENERIC FUNCTIONAL "
                        "CATEGORY names — the element name describes the SLOT in the room, "
                        "not the specific fixture that fills it.\n"
                        "GOOD: floor, walls, ceiling, window, door, lighting, cabinetry\n"
                        "BAD: chandelier, pendant, sconce (use 'lighting').\n"
                        "BAD: hardwood, tile, carpet (use 'floor').\n"
                        "BAD: window frame, window sash (use 'window').\n"
                        "BAD: Wall A drywall, Wall B drywall (use 'walls').\n"
                        "Each element must be a single word or two-word generic label. "
                        "NO specific fixture types, NO materials, NO sub-components. "
                        "STRICTLY 5-7 items.\n"
                        "FEATURE COVERAGE: Every user-requested feature MUST be represented "
                        "in the ELEMENTS list — either as its own element or grouped into an "
                        "existing one. Do not drop any feature the user specified.\n"
                        "FEATURE PROTECTION: User-requested features are DESIRABLE design "
                        "elements. They should be enhanced or highlighted during renovation — "
                        "NEVER removed, covered, or replaced.\n\n"
                        "3. ADDITIONS: From the ELEMENTS list above, list ONLY the elements "
                        "that do NOT currently exist in the space and would be newly added "
                        "during renovation (e.g., cabinetry in a bare room, shelving that "
                        "isn't there yet). If all elements already exist, write 'none'.\n\n"
                        "4. STAGE 1 DESCRIPTION (MAX 200 chars): The current visible state of the "
                        "room BEFORE any renovation. The room is EMPTY — NO loose items, NO "
                        "clutter, NO boxes, NO newspapers, NO debris on the floor. Describe "
                        "only surface-level wear: scuffs, stains, cracks, patchy paint, dated "
                        "fixtures. NO people. Be specific and visual.\n\n"
                        "Respond in EXACTLY this format:\n"
                        "SCENE_BIBLE: [text]\n"
                        "ELEMENTS: [comma-separated list]\n"
                        "ADDITIONS: [comma-separated list or 'none']\n"
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
        additions = ""
        stage_1_desc = ""
        for line in content.split("\n"):
            line = line.strip()
            upper = line.upper()
            if upper.startswith("SCENE_BIBLE:"):
                scene_bible = line[len("SCENE_BIBLE:"):].strip()
            elif upper.startswith("ELEMENTS:"):
                elements = line[len("ELEMENTS:"):].strip()
            elif upper.startswith("ADDITIONS:"):
                additions = line[len("ADDITIONS:"):].strip()
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
        additions_list = [
            a.strip() for a in additions.split(",") if a.strip()
        ] if additions.lower() not in ("none", "") else []

        return {
            "scene_bible": scene_bible,
            "stage_1_description": stage_1_desc,
            "elements": elements_list,
            "additions": additions_list,
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
        user_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        remaining = [e for e in all_elements if e not in renovated_elements]
        remaining_str = ", ".join(remaining) if remaining else "none"
        renovated_str = ", ".join(renovated_elements) if renovated_elements else "none yet"
        stages_left = total_stages - stage_num

        task_focus = (
            "RENOVATION: ADD or UPGRADE elements — install new materials, new "
            "surfaces, new fixtures. Every stage must produce a VISUALLY DRAMATIC, "
            "unmistakable change visible at room scale.\n"
            "VISUAL IMPACT RULE: If an element alone would produce only a subtle "
            "change (e.g., ceiling repaint, swapping a window frame, replacing a "
            "door), group it with other minor elements in ONE stage. Never waste "
            "a stage on a barely-noticeable change. Major surfaces (floor, walls, "
            "full cabinetry) deserve their own stage.\n"
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
                "Pick one high-impact element OR group 2-3 minor elements "
                "that individually would create only a subtle visual change."
            )

        room_state_block = ""
        if room_state:
            room_state_block = (
                f"CURRENT ROOM STATE (for your awareness of what has been done):\n"
                f"{room_state}\n\n"
            )

        protect_rule = ""
        if user_features:
            protect_rule = (
                "- PROTECT: " + ", ".join(user_features)
                + ". Enhance/highlight, never remove/cover/replace. If the element "
                "being renovated shares space with a protected feature, state that "
                "the feature texture itself stays but ALL other surfaces of that "
                "element are fully renovated (e.g. \"renovate all painted wall "
                "surfaces; exposed brick stays as brick but wall paint around it "
                "is resurfaced\").\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an architectural renovation director planning the NEXT "
                    "step in a room timelapse. No people, no workers, no tools — "
                    "renovations happen as if by magic.\n\n"
                    f"Stage {stage_num} of {total_stages}. {task_focus}\n\n"
                    f"Scene: {scene_bible}\n\n"
                    f"{room_state_block}"
                    f"ELEMENTS: {element_rule}\n\n"
                    "RULES:\n"
                    "- Change ONLY the target element's surface treatment (material, "
                    "finish, color, hardware). Physical dimensions, footprint, shape, orientation, "
                    "and structural nature never change — a square element stays square, "
                    "a round one stays round. The image model treats any dimensional "
                    "or shape language as a reshape instruction. Subtle-but-accurate "
                    "beats dramatic-but-structurally-wrong.\n"
                    "- Everything not targeted stays exactly as-is. The image model "
                    "preserves unchanged elements from the previous image automatically.\n"
                    "- For ADDITIONS: specify exact placement (which wall, which area).\n"
                    f"{protect_rule}"
                    "\nProduce SIX things:\n"
                    "1. EDIT (MAX 250 chars): What transforms. No human actions.\n"
                    "2. IMAGE_PROMPT (MAX 200 chars): Short instruction for the image "
                    "model. Describe the target element(s)' final pristine appearance — "
                    "explicitly remove every visible defect from the previous image. "
                    "Use each element's exact canonical name — no qualifiers ('door' "
                    "not 'rear-right door'). End with 'Change nothing else.'\n"
                    f"3. ELEMENT: From [{remaining_str}]. Comma-separated if grouping. Write exactly as shown.\n"
                    "4. MATERIAL (MAX 60 chars): e.g. 'floor: pale porcelain tiles'.\n"
                    "5. PARTIAL: 'yes' if phase 1 of a 2-stage addition, else 'no'.\n"
                    "6. MOTION_PROMPT (MAX 150 chars): Prompt for a video model that "
                    "will generate a time-lapse transition from the PREVIOUS image to "
                    "the NEXT. Describe ONLY the physical renovation process (e.g. "
                    "'old flooring is ripped up and new material is laid down'). "
                    "Do NOT mention final colors, materials, or styles — the video "
                    "model already has the target image. No people, no tools.\n\n"
                    "Respond EXACTLY:\n"
                    "EDIT: [text]\n"
                    "IMAGE_PROMPT: [text]\n"
                    "ELEMENT: [element name(s)]\n"
                    "MATERIAL: [text]\n"
                    "PARTIAL: [yes/no]\n"
                    "MOTION_PROMPT: [text]"
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

        response = None
        api_backoff = 3.0
        for api_attempt in range(4):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.openai_chat_model,
                    messages=messages,
                    temperature=0.7,
                )
                break
            except Exception as exc:
                exc_msg = str(exc).lower()
                is_transient = any(kw in exc_msg for kw in [
                    "timeout", "download", "invalid_image_url",
                    "server_error", "rate_limit", "502", "503", "529",
                ])
                if is_transient and api_attempt < 3:
                    logger.warning(
                        "[GPT] Vision API call failed (attempt %d/4): %s — retrying in %.0fs",
                        api_attempt + 1, exc, api_backoff,
                    )
                    time.sleep(api_backoff)
                    api_backoff *= 2.0
                    continue
                raise

        def _parse_response(content: str):
            ed, ip, el, mat, partial, motion = "", "", "", "", "", ""
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
                elif upper.startswith("MOTION_PROMPT:"):
                    motion = line[len("MOTION_PROMPT:"):].strip()
            return ed, ip, el, mat, partial, motion

        content = response.choices[0].message.content or ""
        edit_delta, image_prompt, element_done, material, partial_flag, motion_prompt = _parse_response(content)

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
                    ed2, ip2, el2, mat2, par2, mot2 = _parse_response(retry_content)
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
                        if not motion_prompt and mot2:
                            motion_prompt = mot2
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
        canonical_list_lower = [e.lower() for e in all_elements]

        def _match_element(raw: str) -> Optional[str]:
            low = raw.lower()
            if low in canonical_set and low != "none":
                return raw
            for canon in canonical_list_lower:
                if low in canon or canon in low:
                    idx = canonical_list_lower.index(canon)
                    logger.info("[GPT] Fuzzy element match: '%s' -> '%s'", raw, all_elements[idx])
                    return all_elements[idx]
            return None

        newly_renovated = []
        for raw in raw_elements:
            matched = _match_element(raw)
            if matched and matched not in newly_renovated:
                newly_renovated.append(matched)

        material_clean = material if material.lower() not in ("none", "") else ""
        is_partial = partial_flag.lower().strip() in ("yes", "true", "1")

        return {
            "edit_delta": edit_delta,
            "image_prompt": image_prompt,
            "renovated_element": newly_renovated,
            "material": material_clean,
            "is_partial": is_partial,
            "motion_prompt": motion_prompt,
        }

    def check_feature_coverage(
        self,
        features: List[str],
        elements: List[str],
        addition_elements: List[str],
    ) -> List[str]:
        """Check which user features are NOT represented in the elements list.

        A feature is 'covered' if an existing element semantically represents it
        (e.g. 'exposed brick' is covered by 'walls'). Returns the list of
        features that have no coverage and need to be force-injected.
        """
        if not features:
            return []

        elements_str = ", ".join(elements)
        additions_str = ", ".join(addition_elements) if addition_elements else "none"
        features_str = ", ".join(features)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are validating a renovation plan.\n\n"
                    f"ELEMENTS planned for renovation: {elements_str}\n"
                    f"ADDITIONS (new elements to add): {additions_str}\n"
                    f"USER-REQUESTED FEATURES: {features_str}\n\n"
                    "For each user feature, decide if it is COVERED by any "
                    "element or addition — either as a direct match or because "
                    "an element semantically represents it (e.g. 'exposed brick' "
                    "is covered by 'walls' since brick is a wall treatment; "
                    "'pendant lights' is covered by 'lighting').\n\n"
                    "List ONLY the user features that are NOT covered by any "
                    "element. Use the exact feature names as provided.\n\n"
                    "If all features are covered, respond with exactly: NONE\n"
                    "Otherwise respond with a comma-separated list of uncovered "
                    "feature names."
                ),
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=0.2,
            )
            content = (response.choices[0].message.content or "").strip()
            logger.info("[GPT] Feature coverage check: %s", content)

            if content.upper() == "NONE":
                return []

            features_lower = {f.lower(): f for f in features}
            missing = []
            for token in content.split(","):
                token_clean = token.strip().lower()
                if token_clean in features_lower:
                    missing.append(features_lower[token_clean])
            return missing
        except Exception as exc:
            logger.warning("[GPT] Feature coverage check failed, skipping: %s", exc)
            return []

    def audit_stage_bleed(
        self,
        prev_image_url: str,
        new_image_url: str,
        targeted_elements: List[str],
        all_elements: List[str],
        renovated_elements: List[str],
    ) -> List[str]:
        """Compare two stage images and return elements that visually changed
        beyond what was targeted (i.e. bleed from the I2I model).

        Returns a list of element names from *remaining* (not yet renovated,
        not targeted this stage) that appear to have been renovated by bleed.
        """
        remaining = [
            e for e in all_elements
            if e not in renovated_elements and e not in targeted_elements
        ]
        if not remaining:
            return []

        remaining_str = ", ".join(remaining)
        targeted_str = ", ".join(targeted_elements)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a visual QA inspector for a renovation timelapse. "
                    "You will see two images: BEFORE and AFTER a renovation stage.\n\n"
                    f"The INTENDED change targeted ONLY: {targeted_str}.\n"
                    f"These elements have NOT been renovated yet: {remaining_str}.\n\n"
                    "Your job: compare the two images and identify which of the "
                    "NOT-YET-RENOVATED elements appear to have ALSO visually changed "
                    "(new paint, new finish, cleaned up, different material, etc.) "
                    "even though they were NOT targeted.\n\n"
                    "Only flag elements with CLEAR, OBVIOUS visual changes — not "
                    "minor lighting shifts or compression artifacts.\n\n"
                    "Respond with ONLY a comma-separated list of element names that "
                    "bled, using the exact names provided. If nothing bled, respond "
                    "with exactly: NONE"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "BEFORE (previous stage):"},
                    {"type": "image_url", "image_url": {"url": prev_image_url}},
                    {"type": "text", "text": "AFTER (current stage):"},
                    {"type": "image_url", "image_url": {"url": new_image_url}},
                ],
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=0.3,
            )
            content = (response.choices[0].message.content or "").strip()
            logger.info("[GPT] Bleed audit result: %s", content)

            if content.upper() == "NONE":
                return []

            remaining_lower = {e.lower(): e for e in remaining}
            bled = []
            for token in content.split(","):
                token = token.strip().lower()
                if token in remaining_lower:
                    bled.append(remaining_lower[token])
            return bled
        except Exception as exc:
            logger.warning("[GPT] Bleed audit failed, skipping: %s", exc)
            return []

    def check_stage_delta(
        self,
        prev_image_url: str,
        new_image_url: str,
        targeted_elements: List[str],
    ) -> bool:
        """Compare two consecutive stage images and return whether
        the visual difference is significant enough to keep.

        Returns True if delta is sufficient, False if the stage
        should be rejected and replanned.
        """
        targeted_str = ", ".join(targeted_elements)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a visual QA inspector for a renovation timelapse video. "
                    "You will see two consecutive frames: BEFORE and AFTER.\n\n"
                    f"The renovation targeted: {targeted_str}.\n\n"
                    "Your job: judge whether a casual viewer scrolling TikTok/Instagram "
                    "would notice a CLEAR, OBVIOUS visual difference between the two "
                    "images at a glance (within 1 second of viewing).\n\n"
                    "Answer PASS if the change is clearly visible at room scale.\n"
                    "Answer FAIL if the images look essentially the same — the change "
                    "is too subtle, too localized, or too similar to the previous state "
                    "to register as a distinct renovation step.\n\n"
                    "Respond with EXACTLY one word: PASS or FAIL"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "BEFORE (previous stage):"},
                    {"type": "image_url", "image_url": {"url": prev_image_url}},
                    {"type": "text", "text": "AFTER (current stage):"},
                    {"type": "image_url", "image_url": {"url": new_image_url}},
                ],
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=0.2,
            )
            content = (response.choices[0].message.content or "").strip().upper()
            logger.info("[GPT] Delta check result: %s (targeted: %s)", content, targeted_str)
            return content.startswith("PASS")
        except Exception as exc:
            logger.warning("[GPT] Delta check failed, accepting stage: %s", exc)
            return True  # fail-open: accept the stage if Vision call errors

    def review_image_prompt(
        self,
        image_prompt: str,
        targeted_elements: List[str],
        all_elements: List[str],
        user_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Strict compliance review of an image_prompt before it reaches the I2I model.
        Returns {"approved": bool, "violations": list[str]}.
        Fail-open: returns approved=True on error.
        """
        targeted_str = ", ".join(targeted_elements) if targeted_elements else "none"
        non_targeted = [e for e in all_elements if e not in targeted_elements]
        non_targeted_str = ", ".join(non_targeted) if non_targeted else "none"
        features_str = ", ".join(user_features) if user_features else "none"

        system_prompt = (
            "You are a QA reviewer for image editing prompts sent to an I2I model. "
            "Focus on catching real mistakes, not nitpicking.\n\n"
            f"TARGET ELEMENTS (allowed to mention): {targeted_str}\n"
            f"NON-TARGET ELEMENTS (MUST NOT appear by name): {non_targeted_str}\n\n"
            "RULES — only reject for clear violations:\n"
            "1. Must end with 'Change nothing else.' — nothing after it.\n"
            "2. Must NOT name any non-target element. 'Keep X unchanged' or 'X stays as-is' "
            "is a VIOLATION — it draws the I2I model's attention to X and causes damage.\n"
            "3. MAX 200 characters total.\n\n"
            "IMPORTANT — these are ALLOWED, do NOT flag them:\n"
            "- Sub-components, materials, finishes, hardware of targeted elements "
            "(e.g. 'shaker doors' on cabinetry, 'low-iron glass' for glazing, 'black pulls' on cabinets)\n"
            "- Describing placement for additions ('on back wall')\n"
            "- Descriptive words about appearance (slim, wide-plank, full-height, flush)\n\n"
            "Respond EXACTLY:\n"
            "VERDICT: [APPROVED or REJECTED]\n"
            "VIOLATIONS: [comma-separated list, or 'none']"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"IMAGE_PROMPT: {image_prompt}"},
                ],
                temperature=0.2,
            )
            content = (response.choices[0].message.content or "").strip()

            verdict, violations_str = "", ""
            for line in content.split("\n"):
                line = line.strip()
                upper = line.upper()
                if upper.startswith("VERDICT:"):
                    verdict = line[len("VERDICT:"):].strip().upper()
                elif upper.startswith("VIOLATIONS:"):
                    violations_str = line[len("VIOLATIONS:"):].strip()

            approved = verdict == "APPROVED"
            violations = [
                v.strip() for v in violations_str.split(",")
                if v.strip() and v.strip().lower() != "none"
            ]

            logger.info("[GPT] Image prompt review: %s (violations: %s)", verdict, violations_str)
            return {"approved": approved, "violations": violations}

        except Exception as exc:
            logger.warning("[GPT] Image prompt review failed, approving by default: %s", exc)
            return {"approved": True, "violations": []}

    def fix_image_prompt(
        self,
        image_prompt: str,
        violations: List[str],
        targeted_elements: List[str],
        all_elements: List[str],
    ) -> str:
        """
        Ask GPT to fix a non-compliant image_prompt given specific violations.
        Returns the corrected prompt. On error, returns the original.
        """
        targeted_str = ", ".join(targeted_elements) if targeted_elements else "none"
        non_targeted = [e for e in all_elements if e not in targeted_elements]
        non_targeted_str = ", ".join(non_targeted) if non_targeted else "none"
        violations_str = "; ".join(violations)

        system_prompt = (
            "Fix the image prompt below. It was rejected for these violations:\n"
            f"{violations_str}\n\n"
            f"TARGET ELEMENTS (allowed to mention): {targeted_str}\n"
            f"NON-TARGET ELEMENTS (must NOT appear): {non_targeted_str}\n\n"
            "RULES for the fixed prompt:\n"
            "- MAX 200 characters\n"
            "- Describe ONLY the target element(s)' final pristine appearance\n"
            "- End with exactly 'Change nothing else.'\n"
            "- Do NOT name any non-target element\n"
            "- Do NOT add new elements or features\n"
            "- Do NOT use dimensional/shape language\n"
            "- Preserve the original renovation intent\n\n"
            "Respond with ONLY:\n"
            "FIXED_PROMPT: [the corrected prompt]"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"IMAGE_PROMPT: {image_prompt}"},
                ],
                temperature=0.4,
            )
            content = (response.choices[0].message.content or "").strip()

            for line in content.split("\n"):
                line = line.strip()
                if line.upper().startswith("FIXED_PROMPT:"):
                    fixed = line[len("FIXED_PROMPT:"):].strip()
                    if fixed:
                        logger.info("[GPT] Fixed image prompt: %s", fixed)
                        return fixed

            logger.warning("[GPT] Could not parse fixed prompt, using original")
            return image_prompt

        except Exception as exc:
            logger.warning("[GPT] Fix image prompt failed, using original: %s", exc)
            return image_prompt

    def generate_transition_prompt(
        self,
        image_url_from: str,
        image_url_to: str,
    ) -> str:
        """
        Send two images to GPT Vision and get back a transition prompt
        suitable for an image-to-video model.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are given two images of the same room at different stages "
                    "of renovation. Write a single short prompt (MAX 150 chars) for "
                    "a video model that will generate a smooth time-lapse transition "
                    "from image 1 to image 2.\n\n"
                    "Rules:\n"
                    "- Describe what changes between the two images.\n"
                    "- No people, no tools, no workers.\n"
                    "- Camera stays fixed. Room structure stays fixed.\n"
                    "- Surfaces and materials transform gradually.\n\n"
                    "Respond with ONLY the prompt text, nothing else."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Image 1 (before):"},
                    {"type": "image_url", "image_url": {"url": image_url_from}},
                    {"type": "text", "text": "Image 2 (after):"},
                    {"type": "image_url", "image_url": {"url": image_url_to}},
                ],
            },
        ]

        api_backoff = 3.0
        for api_attempt in range(4):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.openai_chat_model,
                    messages=messages,
                    temperature=0.7,
                )
                break
            except Exception as exc:
                exc_msg = str(exc).lower()
                is_transient = any(kw in exc_msg for kw in [
                    "timeout", "download", "invalid_image_url",
                    "server_error", "rate_limit", "502", "503", "529",
                ])
                if is_transient and api_attempt < 3:
                    logger.warning(
                        "[GPT] Transition prompt call failed (attempt %d/4): %s — retrying in %.0fs",
                        api_attempt + 1, exc, api_backoff,
                    )
                    time.sleep(api_backoff)
                    api_backoff *= 2.0
                    continue
                raise

        content = response.choices[0].message.content or ""
        prompt = content.strip()
        if not prompt:
            prompt = (
                "Time-lapse transformation: room surfaces and materials smoothly "
                "change. No people, no tools. Camera fixed. Gradual transition."
            )
        return prompt


