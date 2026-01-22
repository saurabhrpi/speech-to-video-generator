from typing import Dict, List, Optional

from ..clients.openai_client import OpenAIClient
from ..clients.aimlapi_client import AIMLAPIClient
from ..utils.config import Settings, get_settings
from ..utils.video import stitch_videos


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

    def generate_superbowl_ad(self, prompt: str) -> Dict:
        """Generate a short ad as 2x4s scenes (Sora 2) and stitch."""
        import os, random
        from ..utils.video import stitch_videos_detailed
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
                status_path="/video/generations/{id}",
                resolution=self.settings.default_resolution_medium,  # e.g., 720p allows 4s
            )
            if not r.get("success"):
                return r
            if r.get("video_url"):
                seg_urls.append(r["video_url"])
        stitched = stitch_videos_detailed(seg_urls)
        if stitched.get("success"):
            return {"success": True, "video_url": "/api/stitched", "segments": seg_urls}
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


