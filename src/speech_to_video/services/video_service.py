import logging
from typing import Callable, Dict, List, Optional

from ..clients.openai_client import OpenAIClient
from ..clients.aimlapi_client import AIMLAPIClient
from ..models.timelapse import TimelapseRequest, compose_timelapse_prompt
from ..utils.config import Settings, get_settings
from ..utils.video import stitch_videos


logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.openai_client = OpenAIClient(self.settings)
        self.aiml_client = AIMLAPIClient(self.settings)

    def speech_to_video_with_audio(self, audio_path: str, duration: int = 60, quality: str = "high") -> Dict:
        transcript = self.openai_client.transcribe(audio_path)
        text = transcript.get("text", "")
        if self.settings.debug_transcript:
            print("[DEBUG] Transcript:", text)
        result = self.generate_video(prompt=text, duration=duration, quality=quality)
        # Include transcript in the final result for UI visibility
        result["transcript"] = text
        return result

    def generate_video(self, prompt: str, duration: int = 60, quality: str = "high") -> Dict:
        if duration <= 10:
            return self._single_generation(prompt, duration, quality)
        return self._multi_generation(prompt, duration, quality)

    def _single_generation(
        self,
        prompt: str,
        duration: int,
        quality: str,
        seed: Optional[int] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        endpoint_path: Optional[str] = None,
        status_path: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> Dict:
        data = self.aiml_client.generate_video(
            prompt=prompt,
            duration=duration,
            quality=quality,
            seed=seed,
            model=model,
            aspect_ratio=aspect_ratio,
            endpoint_path=endpoint_path,
            resolution=resolution,
        )
        status_code = int(data.get("_status_code", 0) or 0)
        # Accept any 2xx as success/created; otherwise return error
        if not (200 <= status_code < 300):
            return {"success": False, "error": data.get("error") or data, "status_code": status_code}

        # v2 returns an id; poll until completion
        job_id = data.get("id") or data.get("job_id") or data.get("generation_id")
        if job_id:
            data = self.aiml_client.poll_until_complete(job_id=str(job_id), status_path=status_path)

        # Determine final video URL if present anywhere in the response structure
        video_url = data.get("video_url")
        if not video_url and hasattr(self.aiml_client, "_extract_video_url"):
            try:
                video_url = self.aiml_client._extract_video_url(data)  # best-effort
            except Exception:
                video_url = None

        # Only treat as success when we have a direct media URL (mp4/webm)
        def _is_media(u: Optional[str]) -> bool:
            if not u:
                return False
            try:
                from urllib.parse import urlparse
                path = urlparse(u).path.lower()
                return path.endswith(".mp4") or path.endswith(".webm")
            except Exception:
                lu = u.lower()
                # Fallback check that tolerates query strings
                import re
                return bool(re.search(r"\.(mp4|webm)(\?|$)", lu))

        is_media = _is_media(video_url)
        if data.get("status") in {"completed", "succeeded", "finished"} and not is_media:
            # Provider finished but didn't return a media URL yet
            return {"success": False, "error": data, "status_code": int(data.get("_status_code", status_code) or status_code)}
        if is_media:
            return {"success": True, "video_url": video_url}

        return {"success": False, "error": data, "status_code": int(data.get("_status_code", status_code) or status_code)}

    def _multi_generation(self, prompt: str, total_duration: int, quality: str) -> Dict:
        scenes = self.openai_client.create_scene_progression(prompt, total_duration)
        video_segments: List[str] = []

        for idx, scene in enumerate(scenes):
            scene_prompt = scene.get("prompt", prompt)
            scene_duration = int(scene.get("duration", 10))
            result = self._single_generation(scene_prompt, scene_duration, quality)
            if not result.get("success"):
                return result
            if result.get("video_url"):
                video_segments.append(result["video_url"])

        final_video = stitch_videos(video_segments)

        return {
            "success": True,
            "video_url": final_video,
            "segments": video_segments,
            "total_duration": total_duration,
        }

    def generate_timelapse(self, request: TimelapseRequest) -> Dict:
        """
        Generate an interior design timelapse video from structured input.
        Composes a rich prompt, then routes to single or multi-phase generation.
        """
        import os
        import random
        from ..utils.video import stitch_videos_seamless

        composed_prompt = compose_timelapse_prompt(request)
        seed = random.randint(1, 2**31 - 1)

        model = os.getenv("TIMELAPSE_MODEL", "openai/sora-2-t2v")
        endpoint_path = os.getenv("TIMELAPSE_ENDPOINT_PATH", "/video/generations")
        status_path = os.getenv("TIMELAPSE_STATUS_PATH", "/video/generations")

        if request.duration <= 12:
            result = self._single_generation(
                composed_prompt,
                request.duration,
                "high",
                seed=seed,
                model=model,
                aspect_ratio="16:9",
                endpoint_path=endpoint_path,
                status_path=status_path,
                resolution=self.settings.default_resolution_medium,
            )
            if result.get("success"):
                result["composed_prompt"] = composed_prompt
                result["seed"] = seed
            return result

        # Multi-phase: use construction-progression scene splitter
        scenes = self.openai_client.create_timelapse_progression(
            composed_prompt, request.duration
        )

        seg_urls: List[str] = []
        for idx, scene in enumerate(scenes):
            scene_prompt = scene.get("prompt", composed_prompt)
            scene_duration = int(scene.get("duration", 10))
            r = self._single_generation(
                scene_prompt,
                scene_duration,
                "high",
                seed=seed,
                model=model,
                aspect_ratio="16:9",
                endpoint_path=endpoint_path,
                status_path=status_path,
                resolution=self.settings.default_resolution_medium,
            )
            if not r.get("success"):
                r["_failed_phase"] = idx + 1
                r["_generated_phases"] = seg_urls
                r["composed_prompt"] = composed_prompt
                return r
            if r.get("video_url"):
                seg_urls.append(r["video_url"])

        stitched = stitch_videos_seamless(seg_urls)
        if stitched.get("success"):
            filename = stitched.get("filename", "stitched_output.mp4")
            return {
                "success": True,
                "video_url": f"/api/stitched/{filename}",
                "segments": seg_urls,
                "duration": request.duration,
                "seed": seed,
                "composed_prompt": composed_prompt,
            }
        return {"success": False, "error": stitched, "composed_prompt": composed_prompt}

    def generate_timelapse_v2(
        self,
        request: TimelapseRequest,
        stop_after: Optional[str] = None,
        resume_state: Optional[Dict] = None,
        on_progress: Optional[Callable] = None,
        video_model: str = "cheap",
    ) -> Dict:
        """
        Iterative timelapse pipeline: GPT plans each stage after seeing the
        previous image, with per-stage pause points.

        stop_after: "plan" | "stage_1" | "stage_2" | ... | "stage_N" | "videos" | None
        resume_state: dict with previously computed partial outputs
        on_progress: callback(phase, step, total, message, partial_result=None)
        """
        import random
        import time as _t
        from ..utils.video import stitch_timelapse_clips

        NUM_STAGES = 7

        def _notify(phase: str, step: int, total: int, message: str, partial_result: Optional[Dict] = None):
            if on_progress:
                on_progress(phase=phase, step=step, total=total, message=message, partial_result=partial_result)

        if not self.settings.aimlapi_api_key:
            return {"success": False, "error": "AIMLAPI key not configured. Set AIMLAPI_API_KEY in .env"}

        resume = resume_state or {}
        seed = resume.get("seed", random.randint(1, 2**31 - 1))

        if resume_state and resume_state.get("video_model"):
            video_model = resume_state["video_model"]

        def _state_snapshot():
            return {
                "scene_bible": scene_bible,
                "elements": list(all_elements),
                "addition_elements": list(addition_elements),
                "renovated_elements": list(renovated_elements),
                "stages": list(stages),
                "seed": seed,
                "keyframe_images": list(keyframe_images),
                "transition_videos": list(transition_videos),
                "transition_prompts": list(transition_prompts),
                "video_model": video_model,
            }

        # --- Phase 1: Scene Bible + Elements + Stage 1 description ---
        scene_bible = resume.get("scene_bible", "")
        all_elements: List[str] = list(resume.get("elements") or [])
        addition_elements: List[str] = list(resume.get("addition_elements") or [])
        renovated_elements: List[str] = list(resume.get("renovated_elements") or [])
        stages: List[Dict] = list(resume.get("stages") or [])
        keyframe_images: List[Dict] = list(resume.get("keyframe_images") or [])
        transition_videos: List[str] = list(resume.get("transition_videos") or [])
        transition_prompts: List[str] = list(resume.get("transition_prompts") or [])

        if not scene_bible:
            _notify("plan", 0, 1, "Generating scene bible, elements + stage 1 description...")
            plan = self.openai_client.generate_scene_bible_only(
                room_type=request.room_type,
                style=request.style,
                features=request.features,
                materials=request.materials,
                lighting=request.lighting,
                camera_motion=request.camera_motion,
                progression=request.progression,
                freeform=request.freeform_description,
            )
            scene_bible = plan["scene_bible"]
            all_elements = plan["elements"]
            addition_elements = plan.get("additions", [])
            stages = [{"stage": 1, "description": plan["stage_1_description"], "edit_delta": ""}]
            logger.info("[Timelapse] Scene bible: %s", scene_bible)
            logger.info("[Timelapse] Elements to renovate: %s", all_elements)
            logger.info("[Timelapse] Addition elements (GPT-classified): %s", addition_elements)
            _notify("plan", 1, 1, "Plan complete", partial_result=_state_snapshot())
        else:
            _notify("plan", 1, 1, f"Using existing plan ({len(stages)} stages)")

        if stop_after == "plan":
            return {
                "success": True, "phase_completed": "plan", "pipeline": "v2",
                **_state_snapshot(),
            }

        # --- Iterative stages: generate image, then plan next stage ---
        completed_stages = len(keyframe_images)

        # Build cumulative room state from completed stages using material summaries
        element_material: Dict[str, str] = {}
        for s in stages:
            mat = s.get("material", "")
            if mat:
                for elem in (s.get("renovated_element") or []):
                    element_material[elem.lower().strip()] = mat

        def _build_room_state() -> str:
            parts = []
            for elem in all_elements:
                key = elem.lower().strip()
                if key in element_material:
                    parts.append(f"{elem} = {element_material[key]}")
                else:
                    parts.append(f"{elem} = original / not yet renovated")
            return "; ".join(parts) if parts else "all elements in original state"

        for stage_idx in range(completed_stages, NUM_STAGES):
            stage_num = stage_idx + 1
            phase_name = f"stage_{stage_num}"

            if stage_idx == 0:
                stage_desc = stages[0]["description"]
                prompt = (
                    f"SAME ROOM, SAME CAMERA, EXACT SAME LAYOUT. {scene_bible} "
                    f"Current state of this room: {stage_desc} "
                    "Empty room, no people."
                )
                _notify(phase_name, 0, 2, f"Stage {stage_num}: generating initial image...")
                logger.info("[Timelapse] Stage %d: T2I via Nano Banana Pro", stage_num)
                img_result = self.aiml_client.generate_image(
                    prompt=prompt, aspect_ratio="16:9", resolution="1K",
                )
            else:
                if stage_idx >= len(stages):
                    prev_img = keyframe_images[-1]
                    prev_desc = stages[-1].get("description", "") or stages[-1].get("edit_delta", "")
                    room_state = _build_room_state()

                    _notify(phase_name, 0, 2, f"Stage {stage_num}: GPT planning next edit...")
                    logger.info("[Timelapse] Stage %d: GPT vision planning", stage_num)
                    logger.info("[Timelapse] Stage %d room state: %s", stage_num, room_state)

                    remaining_now = [e for e in all_elements if e not in renovated_elements]
                    if not remaining_now:
                        logger.info("[Timelapse] Stage %d: all elements renovated, stopping early", stage_num)
                        last_stage_phase = f"stage_{NUM_STAGES}"
                        if stop_after and stop_after.startswith("stage_"):
                            return {
                                "success": True,
                                "phase_completed": last_stage_phase,
                                "pipeline": "v2",
                                "all_images_done": True,
                                **_state_snapshot(),
                            }
                        break

                    addition_names = {a.lower() for a in addition_elements}
                    additions_remaining = [e for e in remaining_now if e.lower() in addition_names]
                    surfaces_remaining = [e for e in remaining_now if e.lower() not in addition_names]
                    stages_left = NUM_STAGES - stage_num
                    addition_stages_needed = len(additions_remaining) * 2
                    total_needed = len(surfaces_remaining) + addition_stages_needed
                    grouping_hint = ""
                    if additions_remaining and total_needed > stages_left + 1:
                        grouping_hint = (
                            f"MANDATORY GROUPING: You have {stages_left + 1} stages left "
                            f"(including this one) but {len(surfaces_remaining)} surfaces "
                            f"({', '.join(surfaces_remaining)}) and "
                            f"{len(additions_remaining)} addition(s) "
                            f"({', '.join(additions_remaining)}) that each need 2 stages. "
                            f"You MUST group 2 surface changes into a single stage NOW to "
                            f"free up a stage for the addition(s)."
                        )
                        logger.info("[Timelapse] Stage %d grouping hint: %s", stage_num, grouping_hint)

                    gpt_result = self.openai_client.generate_next_stage(
                        scene_bible=scene_bible,
                        prev_description=prev_desc,
                        prev_image_url=prev_img["image_url"],
                        stage_num=stage_num,
                        total_stages=NUM_STAGES,
                        all_elements=all_elements,
                        renovated_elements=renovated_elements,
                        room_state=room_state,
                        grouping_hint=grouping_hint,
                        user_features=request.features,
                    )
                    newly_done = gpt_result.get("renovated_element", [])
                    mat_text = gpt_result.get("material", "")
                    is_partial = gpt_result.get("is_partial", False)
                    if not is_partial:
                        for elem in newly_done:
                            if elem not in renovated_elements:
                                renovated_elements.append(elem)
                    if mat_text:
                        for elem in newly_done:
                            element_material[elem.lower().strip()] = mat_text
                    logger.info("[Timelapse] Stage %d element(s): %s | Partial: %s | Renovated so far: %s",
                                stage_num, newly_done, is_partial, renovated_elements)

                    stages.append({
                        "stage": stage_num,
                        "description": gpt_result["edit_delta"],
                        "edit_delta": gpt_result["edit_delta"],
                        "image_prompt": gpt_result.get("image_prompt", gpt_result["edit_delta"]),
                        "renovated_element": newly_done,
                        "material": mat_text,
                        "is_partial": is_partial,
                        "motion_prompt": gpt_result.get("motion_prompt", ""),
                    })

                img_prompt = stages[stage_idx].get("image_prompt") or stages[stage_idx]["edit_delta"]
                prev_image_url = keyframe_images[-1]["image_url"]

                prompt = f"{img_prompt}"
                _notify(phase_name, 1, 2, f"Stage {stage_num}: generating edited image...")
                logger.info("[Timelapse] Stage %d: Edit via Nano Banana Pro Edit", stage_num)
                logger.info("[Timelapse] Stage %d image_prompt: %s", stage_num, img_prompt)
                img_result = self.aiml_client.generate_image(
                    prompt=prompt, image_urls=[prev_image_url],
                    aspect_ratio="16:9", resolution="1K",
                )

            if not img_result.get("success"):
                return {
                    "success": False,
                    "error": f"Image generation failed at stage {stage_num}",
                    "image_error": img_result.get("error"),
                    **_state_snapshot(),
                }

            images = img_result.get("images", [])
            if not images:
                return {
                    "success": False,
                    "error": f"No image URL returned for stage {stage_num}",
                    "raw": img_result,
                    **_state_snapshot(),
                }

            image_url = images[0]
            keyframe_images.append({
                "stage": stage_num,
                "image_url": image_url,
                "description": stages[stage_idx].get("description", ""),
            })
            _notify(phase_name, 2, 2, f"Stage {stage_num} complete", partial_result=_state_snapshot())

            if stop_after == phase_name:
                return {
                    "success": True, "phase_completed": phase_name, "pipeline": "v2",
                    **_state_snapshot(),
                }

        # --- Video transitions via configured I2V model ---
        total_transitions = len(keyframe_images) - 1
        start_idx = len(transition_videos)

        if start_idx >= total_transitions:
            _notify("videos", total_transitions, total_transitions, "All transitions already done")
        elif start_idx > 0:
            logger.info("[Timelapse] Resuming transitions from %d (%d of %d done)",
                        start_idx + 1, start_idx, total_transitions)

        if start_idx < total_transitions:
            camera = request.camera_motion.lower() if request.camera_motion else "static"
            camera_cues = {
                "static": "Static locked-off camera, no camera movement.",
                "slow_pan": "Slow cinematic horizontal pan.",
                "dolly": "Gentle dolly push-in toward the subject.",
                "orbit": "Slow orbit around the scene center.",
                "crane_up": "Smooth crane rise upward revealing the space.",
            }
            camera_instruction = camera_cues.get(camera, camera_cues["static"])
            i2v_model = self.settings.kling_i2v_model if video_model == "expensive" else self.settings.i2v_model
            i2v_resolution = self.settings.i2v_resolution
            i2v_duration = self.settings.i2v_duration

            for i in range(start_idx, total_transitions):
                video_phase = f"video_{i + 1}"
                from_kf = keyframe_images[i]
                to_kf = keyframe_images[i + 1]
                _notify(video_phase, 0, 1,
                        f"Generating transition {i + 1} of {total_transitions}")

                to_stage = stages[i + 1]

                # Use GPT-generated motion prompt (process-only, no materials/styles)
                motion_prompt = to_stage.get("motion_prompt", "")
                if motion_prompt:
                    motion_prompt = f"{motion_prompt} {camera_instruction}"
                else:
                    # Fallback for stages without a motion prompt (e.g. resumed from older state)
                    changed_elements = to_stage.get("renovated_element", [])
                    if changed_elements:
                        motion_prompt = (
                            f"Time-lapse renovation: {', '.join(changed_elements)} "
                            f"are renovated and transformed. Everything else stays "
                            f"exactly the same. No people, no tools. {camera_instruction} "
                            "Room structure stays fixed."
                        )
                    else:
                        motion_prompt = (
                            f"Time-lapse renovation: surfaces transform and upgrade. "
                            f"No people, no tools. {camera_instruction} "
                            "Room structure stays fixed."
                        )
                transition_prompts.append(motion_prompt)

                logger.info("[Timelapse] Generating transition %d->%d (%s)", i + 1, i + 2, i2v_model)
                t0 = _t.time()
                i2v_result = self.aiml_client.generate_and_poll_i2v(
                    image_url=from_kf["image_url"],
                    last_image_url=to_kf["image_url"],
                    prompt=motion_prompt,
                    model=i2v_model,
                    resolution=i2v_resolution,
                    duration=i2v_duration,
                )
                elapsed_s = int(_t.time() - t0)

                if not i2v_result.get("success"):
                    logger.error("[Timelapse] Transition %d->%d FAILED after %ds: %s",
                                 i + 1, i + 2, elapsed_s, i2v_result.get("error"))
                    return {
                        "success": False,
                        "error": f"Transition video failed between stage {i + 1} and {i + 2}",
                        "video_error": i2v_result.get("error"),
                        **_state_snapshot(),
                    }

                video_url = i2v_result.get("video_url")
                if video_url:
                    transition_videos.append(video_url)
                    logger.info("[Timelapse] Transition %d->%d completed in %ds: %s",
                                i + 1, i + 2, elapsed_s, video_url)
                    _notify(video_phase, 1, 1,
                            f"Transition {i + 1} of {total_transitions} complete",
                            partial_result=_state_snapshot())

                if stop_after == video_phase:
                    return {
                        "success": True, "phase_completed": video_phase, "pipeline": "v2",
                        **_state_snapshot(),
                    }

        # --- Final pan shot of the completed room ---
        if keyframe_images and len(transition_videos) == total_transitions:
            _notify("videos", total_transitions, total_transitions + 1,
                    "Generating final reveal pan...")
            logger.info("[Timelapse] Generating final pan shot")
            last_kf = keyframe_images[-1]
            i2v_model = self.settings.kling_i2v_model if video_model == "expensive" else self.settings.i2v_model
            i2v_resolution = self.settings.i2v_resolution

            room_details = _build_room_state()
            pan_prompt = (
                f"Slow gentle camera pan across this exact room. "
                f"Room contents: {room_details}. "
                f"{scene_bible}. "
                "Empty pristine room. Camera glides smoothly. Nothing moves or changes."
            )
            logger.info("[Timelapse] Final pan prompt: %s", pan_prompt)

            t0 = _t.time()
            pan_result = self.aiml_client.generate_and_poll_i2v(
                image_url=last_kf["image_url"],
                prompt=pan_prompt,
                model=i2v_model,
                resolution=i2v_resolution,
                duration=i2v_duration,
                camera_fixed=False,
            )
            elapsed_s = int(_t.time() - t0)
            transition_prompts.append(pan_prompt)
            pan_url = pan_result.get("video_url")
            if pan_url:
                transition_videos.append(pan_url)
                logger.info("[Timelapse] Final pan completed in %ds: %s", elapsed_s, pan_url)
            else:
                logger.warning("[Timelapse] Final pan failed after %ds, skipping: %s",
                               elapsed_s, pan_result.get("error"))

        if not transition_videos:
            return {"success": False, "error": "No transition videos were generated", **_state_snapshot()}

        if stop_after == "videos":
            return {
                "success": True, "phase_completed": "videos", "pipeline": "v2",
                **_state_snapshot(),
            }

        # --- Stitch with 1.5x speed ---
        _notify("stitch", 0, 1, "Stitching videos...")
        stitched = stitch_timelapse_clips(
            video_sources=transition_videos, speed=1.5, dissolve=False,
            hold_first_frame=2.0,
        )

        if stitched.get("success"):
            filename = stitched.get("filename", "stitched_output.mp4")
            _notify("stitch", 1, 1, "Done")
            return {
                "success": True, "phase_completed": "done",
                "video_url": f"/api/stitched/{filename}",
                "pipeline": "v2",
                **_state_snapshot(),
            }
        return {"success": False, "error": stitched.get("error", "Stitching failed"), **_state_snapshot()}

    def generate_custom_videos(
        self,
        image_urls: List[str],
        model: str = "cheap",
        stop_after: Optional[str] = None,
        resume_state: Optional[Dict] = None,
        on_progress: Optional[Callable] = None,
    ) -> Dict:
        """
        Generate transition videos from user-provided ordered images.
        Uses GPT Vision to create transition prompts for each pair.
        Supports step-by-step generation via stop_after/resume_state.
        """
        import time as _t

        def _notify(phase, step, total, message, partial_result=None):
            if on_progress:
                on_progress(phase, step, total, message, partial_result=partial_result)

        transition_videos: List[str] = []
        transition_prompts: List[str] = []
        if resume_state:
            transition_videos = list(resume_state.get("transition_videos") or [])
            transition_prompts = list(resume_state.get("transition_prompts") or [])

        def _state_snapshot():
            return {
                "image_urls": image_urls,
                "model": model,
                "transition_videos": list(transition_videos),
                "transition_prompts": list(transition_prompts),
            }

        total_transitions = len(image_urls) - 1
        start_idx = len(transition_videos)

        if total_transitions < 1:
            return {"success": False, "error": "Need at least 2 images"}

        if start_idx >= total_transitions:
            _notify("videos", total_transitions, total_transitions, "All transitions already done")
            return {
                "success": True, "phase_completed": "all_done",
                **_state_snapshot(),
            }

        resolved_model = self.settings.kling_i2v_model if model == "expensive" else self.settings.i2v_model
        i2v_resolution = self.settings.i2v_resolution
        i2v_duration = self.settings.i2v_duration

        for i in range(start_idx, total_transitions):
            video_phase = f"video_{i + 1}"
            _notify(video_phase, 0, 2,
                    f"GPT analyzing images {i + 1} and {i + 2}...")

            prompt = self.openai_client.generate_transition_prompt(
                image_url_from=image_urls[i],
                image_url_to=image_urls[i + 1],
            )
            transition_prompts.append(prompt)
            logger.info("[CustomVideo] Transition %d->%d prompt: %s", i + 1, i + 2, prompt)

            _notify(video_phase, 1, 2,
                    f"Generating transition video {i + 1} of {total_transitions}...")

            logger.info("[CustomVideo] Generating transition %d->%d (%s)", i + 1, i + 2, resolved_model)
            t0 = _t.time()
            i2v_result = self.aiml_client.generate_and_poll_i2v(
                image_url=image_urls[i],
                last_image_url=image_urls[i + 1],
                prompt=prompt,
                model=resolved_model,
                resolution=i2v_resolution,
                duration=i2v_duration,
            )
            elapsed_s = int(_t.time() - t0)

            if not i2v_result.get("success"):
                logger.error("[CustomVideo] Transition %d->%d FAILED after %ds: %s",
                             i + 1, i + 2, elapsed_s, i2v_result.get("error"))
                return {
                    "success": False,
                    "error": f"Transition video failed between image {i + 1} and {i + 2}",
                    "video_error": i2v_result.get("error"),
                    **_state_snapshot(),
                }

            video_url = i2v_result.get("video_url")
            if video_url:
                transition_videos.append(video_url)
                logger.info("[CustomVideo] Transition %d->%d completed in %ds: %s",
                            i + 1, i + 2, elapsed_s, video_url)
                _notify(video_phase, 2, 2,
                        f"Transition {i + 1} of {total_transitions} complete",
                        partial_result=_state_snapshot())

            if stop_after == video_phase:
                return {
                    "success": True, "phase_completed": video_phase,
                    **_state_snapshot(),
                }

        return {
            "success": True, "phase_completed": "all_done",
            **_state_snapshot(),
        }

    def generate_16s_video(self, prompt: str, seed: Optional[int] = None) -> Dict:
        """
        Generate a seamless 16-second video by creating two 8-second clips with continuity.
        Uses GPT to intelligently split the prompt at a natural narrative break point.
        """
        import os
        import random
        from ..utils.video import stitch_videos_seamless

        # Use provided seed or generate one for consistency across both clips
        if seed is None:
            seed = int(os.getenv("AD_SEED", str(random.randint(1, 2**31 - 1))))

        # Use GPT to intelligently split the prompt into two parts
        split_result = self.openai_client.split_prompt_for_two_clips(prompt)
        clip1_prompt = split_result["clip1"]
        clip2_prompt = split_result["clip2"]

        # Build detailed prompts with strong continuity instructions
        style_instructions = (
            "Cinematic quality, consistent lighting, smooth camera movement. "
            "Maintain exact same visual style, color grading, and atmosphere throughout."
        )

        p1 = (
            f"{clip1_prompt} "
            f"{style_instructions} "
            "This is the FIRST half of a continuous scene."
        )

        p2 = (
            f"{clip2_prompt} "
            f"{style_instructions} "
            "This is the SECOND half continuing EXACTLY from where the first clip ended. "
            "CRITICAL: Use the EXACT same characters, environment, lighting, color palette, "
            "and camera style as the first clip. The transition must be invisible."
        )

        # Generate two 8-second clips
        model = os.getenv("AD_MODEL", "openai/sora-2-t2v")
        endpoint_path = os.getenv("AD_ENDPOINT_PATH", "/video/generations")
        status_path = os.getenv("AD_STATUS_PATH", "/video/generations")

        scenes = [
            {"prompt": p1, "duration": 8},
            {"prompt": p2, "duration": 8},
        ]

        seg_urls: List[str] = []
        for idx, s in enumerate(scenes):
            r = self._single_generation(
                s["prompt"],
                s["duration"],
                "high",
                seed=seed,  # Same seed for both clips
                model=model,
                aspect_ratio="16:9",
                endpoint_path=endpoint_path,
                status_path=status_path,
                resolution=self.settings.default_resolution_medium,
            )
            if not r.get("success"):
                r["_failed_clip"] = idx + 1
                r["_generated_clips"] = seg_urls
                return r
            if r.get("video_url"):
                seg_urls.append(r["video_url"])

        # Stitch seamlessly (no visual crossfade, only subtle audio transitions)
        stitched = stitch_videos_seamless(seg_urls)
        if stitched.get("success"):
            filename = stitched.get("filename", "stitched_output.mp4")
            return {
                "success": True,
                "video_url": f"/api/stitched/{filename}",
                "segments": seg_urls,
                "duration": 16,
                "seed": seed,
            }
        return {"success": False, "error": stitched}

    def generate_superbowl_ad(self, prompt: str) -> Dict:
        """Generate a short ad as 2x4s scenes (Sora 2) and stitch."""
        import os, random
        from ..utils.video import stitch_videos_seamless
        base = self._superbowl_prompt(prompt)
        seed = int(os.getenv("AD_SEED", str(random.randint(1, 2**31 - 1))))
        # Derive strict per-scene prompts from user's script if provided
        import re
        clip1_text, clip2_text = None, None
        try:
            m1 = re.search(r"(?is)\bclip\s*1\b[\s:–—-]*([^]*?)(?=\bclip\s*2\b|$)", prompt)
            m2 = re.search(r"(?is)\bclip\s*2\b[\s:–—-]*([^]*?)$", prompt)
            if m1 and m1.group(1):
                clip1_text = m1.group(1).strip()
            if m2 and m2.group(1):
                clip2_text = m2.group(1).strip()
            if not (clip1_text and clip2_text):
                h1 = re.search(r"(?is)\bthe\s+hook\b[\s:–—-]*([^]*?)(?=\bthe\s+payoff\b|$)", prompt)
                h2 = re.search(r"(?is)\bthe\s+payoff\b[\s:–—-]*([^]*?)$", prompt)
                if h1 and h1.group(1):
                    clip1_text = clip1_text or h1.group(1).strip()
                if h2 and h2.group(1):
                    clip2_text = clip2_text or h2.group(1).strip()
        except Exception:
            pass

        if clip1_text and clip2_text:
            p1 = (
                f"{base} This is Scene 1 (hook). Use ONLY this scene description: {clip1_text}. "
                f"Do NOT include any elements from other scenes. Keep the same hero across scenes."
            )
            p2 = (
                f"{base} This is Scene 2 (payoff/CTA). Use ONLY this scene description: {clip2_text}. "
                f"Do NOT include any elements from other scenes. Keep the same hero across scenes."
            )
        else:
            p1 = (
                f"{base} Scene 1 (hook). Focus solely on the hook beat. "
                f"Do NOT include payoff/endcard elements. Keep the same hero."
            )
            p2 = (
                f"{base} Scene 2 (payoff). Focus solely on payoff/logo/endcard. "
                f"Do NOT include hook elements. Keep the same hero."
            )

        # Two 4-second scenes (lower cost) at 720p, then stitch (~8s total)
        scenes = [
            {"prompt": p1, "duration": 4},
            {"prompt": p2, "duration": 4},
        ]
        seg_urls: List[str] = []
        for s in scenes:
            r = self._single_generation(
                s["prompt"],
                s["duration"],
                "high",
                seed=seed,
                model="openai/sora-2-t2v",
                aspect_ratio="16:9",
                endpoint_path="/video/generations",
                status_path="/video/generations",
                resolution=self.settings.default_resolution_medium,  # e.g., 720p allows 4s
            )
            if not r.get("success"):
                return r
            if r.get("video_url"):
                seg_urls.append(r["video_url"])
        stitched = stitch_videos_seamless(seg_urls)
        if stitched.get("success"):
            filename = stitched.get("filename", "stitched_output.mp4")
            return {"success": True, "video_url": f"/api/stitched/{filename}", "segments": seg_urls}
        return {"success": False, "error": stitched}

    def _superbowl_prompt(self, user_prompt: str) -> str:
        return (
            "Create a cinematic, high-energy 15-second Super Bowl TV ad. "
            "Requirements: 1) Cold open hook in first 2 seconds. "
            "2) Showcase product benefits with dynamic cuts and bold on-screen text. "
            "3) Include diverse shots and quick pacing. 4) Add clear call-to-action near the end. "
            "5) End on hero shot with brand logo. 6) Family-friendly tone. "
            f"Use this brief as the creative direction: {user_prompt}"
        )


