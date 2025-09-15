import json
import traceback
from typing import Optional

import gradio as gr

from ..services.veo3_service import Veo3VideoSystem
from ..utils.config import get_settings


settings = get_settings()
system = Veo3VideoSystem()


def run_speech_to_video(audio_path: str, duration: int, quality: str, prompt: str):
    try:
        manual_prompt = (prompt or "").strip()
        if manual_prompt:
            result = system.generate_veo3_video(prompt=manual_prompt, duration=duration, quality=quality)
            result.setdefault("prompt_used", manual_prompt)
        else:
            if not audio_path:
                return None, json.dumps({"success": False, "error": "No audio provided or prompt supplied"}, indent=2)
            result = system.speech_to_video_with_audio(audio_path=audio_path, duration=duration, quality=quality)
        video = result.get("video_url")
        return video, json.dumps(result, indent=2)
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
        return None, json.dumps(err, indent=2)


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


with gr.Blocks(title="Speech to Video (Veo 3)") as app:
    gr.Markdown("""
    **Speech to Video (Veo 3)**
    
    1. Record or upload an audio clip.
    2. Choose duration and quality.
    3. Generate a video using transcription + Veo 3.
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
            duration = gr.Slider(minimum=5, maximum=120, step=5, value=60, label="Duration (seconds)")
            quality = gr.Dropdown(choices=["high", "medium"], value="high", label="Quality")
            submit = gr.Button("Generate Video")

    with gr.Row():
        video_out = gr.Video(label="Generated Video")
        meta_out = gr.Code(label="Result JSON")

    submit.click(fn=run_speech_to_video, inputs=[audio, duration, quality, prompt], outputs=[video_out, meta_out])


if __name__ == "__main__":
    app.launch()


