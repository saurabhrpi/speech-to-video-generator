from typing import Dict, List, Optional

from ..clients.openai_client import OpenAIClient
from ..clients.aimlapi_client import AIMLAPIClient
from ..utils.config import Settings, get_settings
from ..utils.video import stitch_videos


class Veo3VideoSystem:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.openai_client = OpenAIClient(self.settings)
        self.aiml_client = AIMLAPIClient(self.settings)

    def speech_to_video_with_audio(self, audio_path: str, duration: int = 60, quality: str = "high") -> Dict:
        transcript = self.openai_client.transcribe(audio_path)
        text = transcript.get("text", "")
        if self.settings.debug_transcript:
            print("[DEBUG] Transcript:", text)
        result = self.generate_veo3_video(prompt=text, duration=duration, quality=quality)
        # Include transcript in the final result for UI visibility
        result["transcript"] = text
        return result

    def generate_veo3_video(self, prompt: str, duration: int = 60, quality: str = "high") -> Dict:
        if duration <= 10:
            return self._single_veo3_generation(prompt, duration, quality)
        return self._multi_veo3_generation(prompt, duration, quality)

    def _single_veo3_generation(self, prompt: str, duration: int, quality: str) -> Dict:
        data = self.aiml_client.generate_video(prompt=prompt, duration=duration, quality=quality)
        status_code = data.get("_status_code", 0)
        if status_code != 200:
            return {"success": False, "error": data.get("error") or data, "status_code": status_code}

        # v2 returns an id; poll until completion
        job_id = data.get("id") or data.get("job_id") or data.get("generation_id")
        if job_id:
            data = self.aiml_client.poll_until_complete(job_id=str(job_id))

        # success if a known complete state or a URL is discoverable
        if data.get("status") in {"completed", "succeeded", "finished"} or data.get("video_url"):
            return {
                "success": True,
                "video_url": data.get("video_url"),
                "has_audio": data.get("has_audio", True),
                "duration": duration,
                "cost": duration * 0.788,
            }

        return {"success": False, "error": data}

    def _multi_veo3_generation(self, prompt: str, total_duration: int, quality: str) -> Dict:
        scenes = self.openai_client.create_scene_progression(prompt, total_duration)
        video_segments: List[str] = []
        total_cost = 0.0

        for idx, scene in enumerate(scenes):
            scene_prompt = scene.get("prompt", prompt)
            scene_duration = int(scene.get("duration", 10))
            result = self._single_veo3_generation(scene_prompt, scene_duration, quality)
            if not result.get("success"):
                return result
            if result.get("video_url"):
                video_segments.append(result["video_url"])
            total_cost += float(result.get("cost", 0.0))

        final_video = stitch_videos(video_segments)

        return {
            "success": True,
            "video_url": final_video,
            "segments": video_segments,
            "total_duration": total_duration,
            "total_cost": total_cost,
            "has_audio": True,
        }


