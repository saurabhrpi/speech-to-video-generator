import os
import tempfile
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse
import requests

from ..services.video_service import VideoService
from ..utils.config import get_settings
from ..utils.clip_store import add_clip, list_clips, clear_clips
from ..utils.video import stitch_videos_detailed


settings = get_settings()
service = VideoService(settings)

app = FastAPI(title="Speech to Video API")


# CORS for local dev (Vite default origin)
_default_cors = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", ",".join(_default_cors)).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/setup")
def setup_status():
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
    return {"env": info}


@app.post("/api/generate")
def generate_video(prompt: str = Form(...), duration: int = Form(10), quality: str = Form("high")):
    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt is required")
    result = service.generate_video(prompt=prompt.strip(), duration=int(duration), quality=quality)
    return JSONResponse(result)


@app.post("/api/speech-to-video")
async def speech_to_video(
    audio: UploadFile = File(...),
    duration: int = Form(10),
    quality: str = Form("high"),
    prompt: Optional[str] = Form(None),
):
    # Save upload to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename or "")[1] or ".wav") as tmpf:
            contents = await audio.read()
            tmpf.write(contents)
            tmp_path = tmpf.name
    finally:
        try:
            await audio.close()
        except Exception:
            pass

    try:
        if prompt and prompt.strip():
            result = service.generate_video(prompt=prompt.strip(), duration=int(duration), quality=quality)
        else:
            result = service.speech_to_video_with_audio(audio_path=tmp_path, duration=int(duration), quality=quality)
        return JSONResponse(result)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@app.get("/api/clips")
def get_clips():
    return JSONResponse(list_clips())


@app.post("/api/clips")
def save_clip(url: str = Form(...), note: Optional[str] = Form(None)):
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    entry = add_clip(url, note)
    return JSONResponse({"success": True, "saved": entry})


@app.delete("/api/clips")
def delete_clips():
    clear_clips()
    return JSONResponse({"success": True, "cleared": True})


@app.post("/api/stitch")
def stitch(urls: Optional[str] = Form(None), use_saved: bool = Form(False)):
    url_list: List[str] = []
    if use_saved:
        items = list_clips()
        url_list = [i.get("url") for i in items if i.get("url")]
    else:
        if urls:
            # Accept comma or newline separated
            parts = [p.strip() for p in urls.replace("\n", ",").split(",")]
            url_list = [p for p in parts if p]
    if not url_list:
        raise HTTPException(status_code=400, detail="No URLs to stitch")
    detailed = stitch_videos_detailed(url_list)
    return JSONResponse(detailed)


@app.get("/api/stitched")
def get_stitched_file():
    path = os.path.abspath("stitched_output.mp4")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No stitched_output.mp4 found")
    return FileResponse(path, media_type="video/mp4", filename="stitched_output.mp4")


@app.get("/api/proxy-video")
def proxy_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    try:
        r = requests.get(url, stream=True, timeout=600)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Upstream fetch failed: {exc}")

    status = r.status_code
    if status >= 400:
        raise HTTPException(status_code=status, detail=f"Upstream returned {status}")

    headers = {}
    ct = r.headers.get("Content-Type")
    if ct:
        headers["Content-Type"] = ct
    cl = r.headers.get("Content-Length")
    if cl:
        headers["Content-Length"] = cl

    return StreamingResponse(r.iter_content(chunk_size=8192), headers=headers, status_code=status)


# Optionally mount Gradio UI at /gradio for transition
try:
    import gradio as gr  # type: ignore
    from ..webui.app import app as gradio_blocks

    app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")
except Exception:
    # Gradio optional; ignore if not present
    pass


def _mount_static(app_: FastAPI) -> None:
    try:
        web_dist = os.path.abspath(os.path.join(os.getcwd(), "web", "dist"))
        if os.path.isdir(web_dist) and os.listdir(web_dist):
            app_.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    except Exception:
        # Serving static is best-effort
        pass


_mount_static(app)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("src.speech_to_video.api.server:app", host=host, port=port, reload=os.getenv("RELOAD", "0") in {"1", "true", "on", "yes"})


