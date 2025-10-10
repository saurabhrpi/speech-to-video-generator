import json
import traceback
from typing import Optional

import gradio as gr

from ..services.video_service import VideoService
from ..utils.config import get_settings
from ..utils.video import stitch_videos, stitch_videos_detailed
from ..utils.clip_store import add_clip, list_clips, clear_clips


settings = get_settings()
system = VideoService()


def run_speech_to_video(audio_path: str, prompt: str):
    try:
        manual_prompt = (prompt or "").strip()
        if manual_prompt:
            # Use a single-clip call; many providers ignore duration, but 10s keeps us on single path
            result = system.generate_video(prompt=manual_prompt, duration=10)
            result.setdefault("prompt_used", manual_prompt)
        else:
            if not audio_path:
                return None, json.dumps({"success": False, "error": "No audio provided or prompt supplied"}, indent=2), None
            result = system.speech_to_video_with_audio(audio_path=audio_path, duration=10)
        video = result.get("video_url")
        return video, json.dumps(result, indent=2), video
    except Exception as exc:
        err = {
            "success": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
            "hints": [
                "Verify OPENAI_API_KEY and AIMLAPI_API_KEY are set in .env",
                "Ensure internet connectivity",
                "If stitching is enabled, verify ffmpeg is installed (moviepy)",
            ],
        }
        msg = str(exc).lower()
        if "insufficient_quota" in msg or "error code: 429" in msg or "rate limit" in msg:
            err.setdefault("hints", []).extend([
                "OpenAI quota exceeded: add billing/credits or wait/reset",
                "Enter a Prompt in the UI to bypass transcription (uses AIMLAPI only)",
                "Or use CLI: python -m src.speech_to_video.cli generate --prompt '...' --duration 10",
            ])
        if "503" in msg or "service unavailable" in msg or "unexpected error occurred" in msg:
            err.setdefault("hints", []).extend([
                "AIMLAPI returned 503: temporary service issue",
                "Please try again in a minute",
            ])
        return None, json.dumps(err, indent=2), None


def check_setup():
    info = {
        "openai_api_key_present": bool(settings.openai_api_key),
        "openai_org_id_present": bool(getattr(settings, "openai_org_id", "")),
        "openai_project_present": bool(getattr(settings, "openai_project", "")),
        "aimlapi_api_key_present": bool(settings.aimlapi_api_key),
        "aimlapi_base_url": settings.aimlapi_base_url,
        "aimlapi_generate_path": settings.aimlapi_generate_path,
        "aimlapi_status_path": settings.aimlapi_status_path,
        "openai_chat_model": settings.openai_chat_model,
        "openai_transcribe_model": settings.openai_transcribe_model,
    }
    tips = []
    if not info["openai_api_key_present"]:
        tips.append("Set OPENAI_API_KEY in .env (then restart app)")
    if not info["openai_org_id_present"]:
        tips.append("Optionally set OPENAI_ORG_ID if your org requires it")
    if not info["openai_project_present"]:
        tips.append("Optionally set OPENAI_PROJECT for project-scoped keys (sk-proj-...)")
    if not info["aimlapi_api_key_present"]:
        tips.append("Set AIMLAPI_API_KEY in .env (then restart app)")
    return json.dumps({"env": info, "tips": tips}, indent=2)


def test_openai_key():
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key,
            organization=(getattr(settings, "openai_org_id", "") or None),
            project=(getattr(settings, "openai_project", "") or None),
        )
        models = client.models.list()
        count = len(getattr(models, "data", []) or [])
        return json.dumps({"success": True, "models_count": count}, indent=2)
    except Exception as exc:
        return json.dumps({"success": False, "error": str(exc)}, indent=2)


def test_aimlapi_paths():
    try:
        client = system.aiml_client
        # Probe generate with a dry-run-like tiny prompt and duration=1 (provider may ignore)
        data = client.generate_video(prompt="ping", duration=1, quality="medium")
        return json.dumps({"response": data}, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc)}, indent=2)


with gr.Blocks(title="Speech to Video (WAN 2.1 Turbo)") as app:
    gr.Markdown("""
    **Speech to Video (WAN 2.1 Turbo)**
    
    1. Record or upload an audio clip, or provide a prompt.
    2. Generate a video using WAN 2.1 Turbo.
    """)

    with gr.Accordion("Setup status", open=False):
        setup_box = gr.Code(label="Environment checks", value=check_setup())
        with gr.Row():
            refresh = gr.Button("Refresh checks")
            test_key = gr.Button("Test OpenAI Key")
            test_aiml = gr.Button("Test AIMLAPI Paths")
        test_out = gr.Code(label="OpenAI test result")
        test_aiml_out = gr.Code(label="AIMLAPI test result")
        refresh.click(fn=check_setup, inputs=None, outputs=setup_box)
        test_key.click(fn=test_openai_key, inputs=None, outputs=test_out)
        test_aiml.click(fn=test_aimlapi_paths, inputs=None, outputs=test_aiml_out)

    with gr.Row():
        audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Speech audio")
        with gr.Column():
            prompt = gr.Textbox(label="Prompt (optional; bypasses transcription)")
            submit = gr.Button("Generate Video")

    with gr.Row():
        video_out = gr.Video(label="Generated Video")
        meta_out = gr.Code(label="Result JSON")

    # track last clip url
    last_clip_url = gr.State(None)
    submit.click(fn=run_speech_to_video, inputs=[audio, prompt], outputs=[video_out, meta_out, last_clip_url])

    def _save_last_clip(note: str, url):
        if not url:
            return json.dumps({"success": False, "error": "No last clip to save"}, indent=2), json.dumps(list_clips(), indent=2)
        entry = add_clip(url, note)
        return json.dumps({"success": True, "saved": entry}, indent=2), json.dumps(list_clips(), indent=2)

    def _show_clips():
        return json.dumps(list_clips(), indent=2)

    def _clear_all_clips():
        clear_clips()
        return json.dumps({"success": True, "cleared": True}, indent=2), json.dumps(list_clips(), indent=2)

    def _stitch_saved():
        items = list_clips()
        urls = [i.get("url") for i in items if i.get("url")]
        if not urls:
            return None, json.dumps({"success": False, "error": "No saved clips"}, indent=2)
        detailed = stitch_videos_detailed(urls)
        if not detailed.get("success"):
            return None, json.dumps(detailed, indent=2)
        return detailed.get("output_path"), json.dumps(detailed, indent=2)

    with gr.Accordion("Clip library", open=False):
        note = gr.Textbox(label="Note (optional)")
        save_btn = gr.Button("Save last clip")
        saved_status = gr.Code(label="Save status")
        saved_list = gr.Code(label="Saved clips")
        list_btn = gr.Button("Refresh list")
        clear_btn = gr.Button("Clear all")
        stitch_btn = gr.Button("Stitch saved clips")
        stitched_video = gr.Video(label="Stitched video")
        stitched_json = gr.Code(label="Stitch result JSON")

        save_btn.click(fn=_save_last_clip, inputs=[note, last_clip_url], outputs=[saved_status, saved_list])
        list_btn.click(fn=_show_clips, inputs=None, outputs=[saved_list])
        clear_btn.click(fn=_clear_all_clips, inputs=None, outputs=[saved_status, saved_list])
        stitch_btn.click(fn=_stitch_saved, inputs=None, outputs=[stitched_video, stitched_json])


if __name__ == "__main__":
    app.launch()


