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
    ) -> Dict:
        """
        Multi-step timelapse pipeline with optional pause points.

        stop_after: "plan" | "images" | "videos" | None (run all phases)
        resume_state: dict with previously computed outputs to skip phases:
            - scene_bible, stages, seed  -> skip Phase 1
            - keyframe_images            -> skip Phase 2
            - transition_videos          -> skip Phase 3
        on_progress: callback(phase, step, total, message, partial_result=None)
        """
        import random
        from ..utils.video import stitch_timelapse_clips

        def _notify(phase: str, step: int, total: int, message: str, partial_result: Optional[Dict] = None):
            if on_progress:
                on_progress(phase=phase, step=step, total=total, message=message, partial_result=partial_result)

        if not self.settings.aimlapi_api_key:
            return {"success": False, "error": "AIMLAPI key not configured. Set AIMLAPI_API_KEY in .env"}

        resume = resume_state or {}

        # --- Phase 1: Generate Scene Bible + stage deltas via GPT ---
        if "scene_bible" in resume and "stages" in resume:
            scene_bible = resume["scene_bible"]
            stages = resume["stages"]
            seed = resume.get("seed", random.randint(1, 2**31 - 1))
            num_stages = len(stages)
            logger.info("[Timelapse] Resuming with existing plan (%d stages)", num_stages)
            _notify("plan", 1, 1, f"Using existing plan ({num_stages} stages)")
        else:
            _notify("plan", 0, 1, "Generating plan via GPT...")
            seed = random.randint(1, 2**31 - 1)
            num_stages = 7
            plan = self.openai_client.generate_scene_bible_and_stages(
                room_type=request.room_type,
                style=request.style,
                features=request.features,
                materials=request.materials,
                lighting=request.lighting,
                camera_motion=request.camera_motion,
                progression=request.progression,
                num_stages=num_stages,
                freeform=request.freeform_description,
            )
            scene_bible = plan["scene_bible"]
            stages = plan["stages"]
            _notify("plan", 1, 1, "Plan complete", partial_result={
                "scene_bible": scene_bible, "stages": stages, "seed": seed,
            })

        if stop_after == "plan":
            return {
                "success": True,
                "phase_completed": "plan",
                "scene_bible": scene_bible,
                "stages": stages,
                "seed": seed,
                "pipeline": "v2",
            }

        # --- Phase 2: Generate keyframe images via Nano Banana Pro ---
        if "keyframe_images" in resume and resume["keyframe_images"]:
            keyframe_images = resume["keyframe_images"]
            logger.info("[Timelapse] Resuming with %d existing keyframe images", len(keyframe_images))
            _notify("images", len(keyframe_images), len(keyframe_images), f"Using {len(keyframe_images)} existing images")
        else:
            keyframe_images: List[Dict] = []
            prev_image_url: Optional[str] = None

            for i, stage in enumerate(stages):
                stage_desc = stage.get("description", "")
                edit_delta = stage.get("edit_delta", "")
                _notify("images", i, len(stages), f"Generating image {i + 1} of {len(stages)}")

                if i == 0:
                    prompt = (
                        f"SAME ROOM, SAME CAMERA, EXACT SAME LAYOUT. {scene_bible} "
                        f"Current state of this room: {stage_desc}"
                    )
                    logger.info("[Timelapse] Stage %d: T2I via Nano Banana Pro", i + 1)
                    img_result = self.aiml_client.generate_image(
                        prompt=prompt,
                        aspect_ratio="16:9",
                        resolution="1K",
                    )
                else:
                    if prev_image_url is None:
                        return {
                            "success": False,
                            "error": f"No image URL from stage {i} to use as reference",
                            "scene_bible": scene_bible,
                            "stages": stages,
                        }
                    prompt = (
                        f"In this image, make the following changes: {edit_delta} "
                        f"Keep everything else in the image exactly the same."
                    )
                    logger.info("[Timelapse] Stage %d: Edit via Nano Banana Pro Edit", i + 1)
                    img_result = self.aiml_client.generate_image(
                        prompt=prompt,
                        image_urls=[prev_image_url],
                        aspect_ratio="16:9",
                        resolution="1K",
                    )

                if not img_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Image generation failed at stage {i + 1}",
                        "image_error": img_result.get("error"),
                        "scene_bible": scene_bible,
                        "stages": stages,
                        "seed": seed,
                        "keyframe_images": keyframe_images,
                        "_completed_keyframes": len(keyframe_images),
                    }

                images = img_result.get("images", [])
                if not images:
                    return {
                        "success": False,
                        "error": f"No image URL returned for stage {i + 1}",
                        "raw": img_result,
                        "_completed_keyframes": len(keyframe_images),
                    }

                image_url = images[0]
                keyframe_images.append({
                    "stage": i + 1,
                    "image_url": image_url,
                    "description": stage_desc,
                })
                prev_image_url = image_url

            _notify("images", len(stages), len(stages), "All images generated", partial_result={
                "scene_bible": scene_bible, "stages": stages, "seed": seed,
                "keyframe_images": keyframe_images,
            })

        if stop_after == "images":
            return {
                "success": True,
                "phase_completed": "images",
                "scene_bible": scene_bible,
                "stages": stages,
                "seed": seed,
                "keyframe_images": keyframe_images,
                "pipeline": "v2",
            }

        # --- Phase 3: Generate transition videos via Kling (first+last frame) ---
        total_transitions_needed = len(keyframe_images) - 1
        transition_videos: List[str] = list(resume.get("transition_videos") or [])
        start_idx = len(transition_videos)

        if start_idx >= total_transitions_needed:
            logger.info("[Timelapse] Resuming with all %d transition videos already done", len(transition_videos))
            _notify("videos", total_transitions_needed, total_transitions_needed, "All transitions already done")
        elif start_idx > 0:
            logger.info("[Timelapse] Resuming transitions from %d->%d (%d of %d done)",
                        start_idx + 1, start_idx + 2, start_idx, total_transitions_needed)
        else:
            pass

        if start_idx < total_transitions_needed:
            camera = request.camera_motion.lower() if request.camera_motion else "static"
            camera_cues = {
                "static": "Static locked-off camera, no camera movement.",
                "slow_pan": "Slow cinematic horizontal pan.",
                "dolly": "Gentle dolly push-in toward the subject.",
                "orbit": "Slow orbit around the scene center.",
                "crane_up": "Smooth crane rise upward revealing the space.",
            }
            camera_instruction = camera_cues.get(camera, camera_cues["static"])

            for i in range(start_idx, total_transitions_needed):
                from_kf = keyframe_images[i]
                to_kf = keyframe_images[i + 1]

                _notify("videos", i, total_transitions_needed,
                        f"Generating transition {i + 1} of {total_transitions_needed}")

                transition_prompt = stages[i].get("transition_prompt", "")
                if not transition_prompt:
                    transition_prompt = (
                        "Smooth timelapse transformation, gradual material changes, "
                        "architectural elements morphing into place."
                    )

                motion_prompt = (
                    f"Timelapse transition: {transition_prompt} "
                    f"{camera_instruction} "
                    "Smooth continuous transformation preserving room geometry."
                )

                logger.info(
                    "[Timelapse] Generating transition %d->%d with first+last frame",
                    i + 1, i + 2,
                )

                import time as _t
                t0 = _t.time()
                i2v_result = self.aiml_client.generate_and_poll_i2v(
                    image_url=from_kf["image_url"],
                    last_image_url=to_kf["image_url"],
                    prompt=motion_prompt,
                )
                elapsed_s = int(_t.time() - t0)

                if not i2v_result.get("success"):
                    logger.error(
                        "[Timelapse] Transition %d->%d FAILED after %ds: %s",
                        i + 1, i + 2, elapsed_s, i2v_result.get("error"),
                    )
                    return {
                        "success": False,
                        "error": f"Transition video failed between stage {i + 1} and {i + 2}",
                        "kling_error": i2v_result.get("error"),
                        "keyframe_images": keyframe_images,
                        "scene_bible": scene_bible,
                        "stages": stages,
                        "seed": seed,
                        "_completed_transitions": len(transition_videos),
                        "transition_videos": transition_videos,
                    }

                video_url = i2v_result.get("video_url")
                if video_url:
                    transition_videos.append(video_url)
                    logger.info(
                        "[Timelapse] Transition %d->%d completed in %ds: %s",
                        i + 1, i + 2, elapsed_s, video_url,
                    )
                    _notify("videos", i + 1, total_transitions_needed,
                            f"Transition {i + 1} of {total_transitions_needed} complete",
                            partial_result={
                                "scene_bible": scene_bible, "stages": stages, "seed": seed,
                                "keyframe_images": keyframe_images,
                                "transition_videos": list(transition_videos),
                            })

        if not transition_videos:
            return {
                "success": False,
                "error": "No transition videos were generated",
                "keyframe_images": keyframe_images,
                "scene_bible": scene_bible,
                "stages": stages,
                "seed": seed,
            }

        if stop_after == "videos":
            return {
                "success": True,
                "phase_completed": "videos",
                "scene_bible": scene_bible,
                "stages": stages,
                "seed": seed,
                "keyframe_images": keyframe_images,
                "transition_videos": transition_videos,
                "pipeline": "v2",
            }

        # --- Phase 4: Stitch with 1.5x speed ---
        _notify("stitch", 0, 1, "Stitching videos...")
        stitched = stitch_timelapse_clips(
            video_sources=transition_videos,
            speed=1.5,
            dissolve=False,
        )

        if stitched.get("success"):
            filename = stitched.get("filename", "stitched_output.mp4")
            _notify("stitch", 1, 1, "Done")
            return {
                "success": True,
                "phase_completed": "done",
                "video_url": f"/api/stitched/{filename}",
                "keyframe_images": keyframe_images,
                "transition_videos": transition_videos,
                "scene_bible": scene_bible,
                "stages": stages,
                "seed": seed,
                "pipeline": "v2",
            }
        return {
            "success": False,
            "error": stitched.get("error", "Stitching failed"),
            "keyframe_images": keyframe_images,
            "transition_videos": transition_videos,
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


