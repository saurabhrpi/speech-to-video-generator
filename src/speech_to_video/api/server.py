import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

from logging.handlers import RotatingFileHandler
import pathlib

_LOG_DIR = pathlib.Path(__file__).resolve().parents[3] / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_fmt = "%(asctime)s %(name)s %(levelname)s %(message)s"
logging.basicConfig(level=logging.INFO, format=_fmt, handlers=[
    logging.StreamHandler(),
    RotatingFileHandler(_LOG_DIR / "app.log", maxBytes=5_000_000, backupCount=3),
])
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse
import requests
import shutil
import glob

from ..services.video_service import VideoService
from ..models.timelapse import TimelapseRequest, get_all_options
from ..utils.config import get_settings
from ..utils.clip_store import add_clip, list_clips, clear_clips, reorder_clips, remove_stitched_clips, remove_clip, get_response
from ..utils.video import stitch_videos_detailed, stitch_timelapse_clips
from .firebase_auth import verify_firebase_token


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
        "firebase_service_account_present": bool(
            getattr(settings, "firebase_service_account_json", "")
            or getattr(settings, "firebase_service_account_path", "")
        ),
        "firebase_credentials_source": (
            "json_env" if getattr(settings, "firebase_service_account_json", "")
            else ("path" if getattr(settings, "firebase_service_account_path", "") else "missing")
        ),
    }
    return {"env": info}


# --------- Auth and usage limiting (Firebase-based) ---------
_UNAUTH_LIMIT = int(os.getenv("UNAUTH_GEN_LIMIT", "1"))
# Per-UID usage bucket. Only anonymous users are limited; signed-in are unlimited.
_UID_USAGE: dict[str, int] = {}


def _get_usage(uid: str) -> int:
    return int(_UID_USAGE.get(uid, 0))


def _inc_usage(user: Dict) -> int:
    """Increment usage for anonymous users only. No-op for signed-in users."""
    if not user.get("is_anonymous"):
        return 0
    uid = user["uid"]
    _UID_USAGE[uid] = _UID_USAGE.get(uid, 0) + 1
    return _UID_USAGE[uid]


def _check_usage_or_401(user: Dict) -> None:
    if user.get("is_anonymous") and _get_usage(user["uid"]) >= _UNAUTH_LIMIT:
        raise HTTPException(status_code=401, detail="login_required")


def _user_namespace(user: Dict) -> Optional[str]:
    """Build clip-store namespace: env-prefix / firebase-uid."""
    ns = os.getenv("CLIPS_NAMESPACE", "")
    uid = user["uid"]
    return "/".join([p for p in [ns, uid] if p]) or None


@app.get("/api/auth/session")
def auth_session(user: Dict = Depends(verify_firebase_token)):
    return {
        "uid": user["uid"],
        "is_anonymous": user["is_anonymous"],
        "email": user.get("email"),
        "name": user.get("name"),
        "provider": user.get("provider"),
        "usage_count": _get_usage(user["uid"]),
        "limit": _UNAUTH_LIMIT,
    }


@app.post("/api/generate")
def generate_video(
    prompt: str = Form(...),
    duration: int = Form(10),
    quality: str = Form("high"),
    user: Dict = Depends(verify_firebase_token),
):
    _check_usage_or_401(user)
    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt is required")
    result = service.generate_video(prompt=prompt.strip(), duration=int(duration), quality=quality)
    if result.get("success") or result.get("video_url"):
        _inc_usage(user)
    return JSONResponse(result)


@app.post("/api/speech-to-video")
async def speech_to_video(
    audio: UploadFile = File(...),
    duration: int = Form(10),
    quality: str = Form("high"),
    prompt: Optional[str] = Form(None),
    user: Dict = Depends(verify_firebase_token),
):
    _check_usage_or_401(user)
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
        if result.get("success") or result.get("video_url"):
            _inc_usage(user)
        return JSONResponse(result)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@app.get("/api/clips")
def get_clips(user: Dict = Depends(verify_firebase_token)):
    return JSONResponse(list_clips(_user_namespace(user)))


@app.post("/api/clips")
def save_clip(
    url: str = Form(...),
    note: Optional[str] = Form(None),
    json_response: Optional[str] = Form(None),
    user: Dict = Depends(verify_firebase_token),
):
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    entry = add_clip(url, note, _user_namespace(user), json_response=json_response)
    return JSONResponse({"success": True, "saved": entry})


@app.get("/api/clips/{ts}/response")
def get_clip_response(ts: int, user: Dict = Depends(verify_firebase_token)):
    content = get_response(ts, _user_namespace(user))
    if content is None:
        raise HTTPException(status_code=404, detail="No saved response for this clip")
    return JSONResponse(json.loads(content))


@app.delete("/api/clips")
def delete_clips(user: Dict = Depends(verify_firebase_token)):
    clear_clips(_user_namespace(user))
    return JSONResponse({"success": True, "cleared": True})


@app.delete("/api/clips/{ts}")
def delete_clip(ts: int, user: Dict = Depends(verify_firebase_token)):
    try:
        ok = remove_clip(ts, _user_namespace(user))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to delete: {exc}")
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return JSONResponse({"success": True})


@app.post("/api/clips/reorder")
def clips_reorder(order: str = Form(...), user: Dict = Depends(verify_firebase_token)):
    namespace = _user_namespace(user)
    order_ts: list[int] = []
    s = (order or "").strip()
    if s.startswith("["):
        try:
            arr = json.loads(s)
            order_ts = [int(x) for x in arr if isinstance(x, (int, float, str))]
        except Exception:
            order_ts = []
    else:
        parts = [p.strip() for p in s.split(",")]
        for p in parts:
            try:
                order_ts.append(int(p))
            except Exception:
                pass
    if not order_ts:
        raise HTTPException(status_code=400, detail="invalid order")
    new_items = reorder_clips(order_ts, namespace)
    return JSONResponse({"success": True, "clips": new_items})


@app.post("/api/stitch")
def stitch(
    urls: Optional[str] = Form(None),
    use_saved: bool = Form(False),
    user: Dict = Depends(verify_firebase_token),
):
    url_list: List[str] = []
    namespace = _user_namespace(user)
    if use_saved:
        items = list_clips(namespace)
        filtered: List[str] = []
        for i in items:
            u = (i.get("url") or "").strip()
            note = (i.get("note") or "").strip().lower()
            if not u:
                continue
            if u.startswith("/api/stitched") or u.endswith("/api/stitched"):
                continue
            if "stitched" in note:
                continue
            if not (u.startswith("http://") or u.startswith("https://")):
                continue
            filtered.append(u)
        seen = set()
        url_list = [x for x in filtered if not (x in seen or seen.add(x))]
    else:
        if urls:
            parts = [p.strip() for p in urls.replace("\n", ",").split(",")]
            url_list = [p for p in parts if p and (p.startswith("http://") or p.startswith("https://"))]
    if not url_list:
        raise HTTPException(status_code=400, detail="No URLs to stitch")
    detailed = stitch_videos_detailed(url_list)
    if detailed.get("success") and detailed.get("output_path"):
        out_path = detailed.get("output_path")
        base_dir = os.getenv("CLIPS_DIR") or os.path.join(os.path.abspath(os.getcwd()), "clips")
        target_dir = os.path.join(base_dir, *(namespace.split("/") if namespace else []), "stitched")
        os.makedirs(target_dir, exist_ok=True)
        fname = f"stitched-{int(time.time())}.mp4"
        dest = os.path.join(target_dir, fname)
        try:
            shutil.copyfile(out_path, dest)
            detailed["stitched_url"] = f"/api/stitched/{fname}"
            try:
                remove_stitched_clips(namespace)
            except Exception:
                pass
        except Exception as exc:
            detailed.setdefault("error", str(exc))
    return JSONResponse(detailed)


@app.get("/api/stitched")
def get_stitched_file(user: Dict = Depends(verify_firebase_token)):
    namespace = _user_namespace(user) or ""
    base_dir = os.getenv("CLIPS_DIR") or os.path.join(os.path.abspath(os.getcwd()), "clips")
    target_dir = os.path.join(base_dir, *(namespace.split("/") if namespace else []), "stitched")
    if os.path.isdir(target_dir):
        files = sorted(glob.glob(os.path.join(target_dir, "stitched-*.mp4")))
        if files:
            latest = files[-1]
            return FileResponse(latest, media_type="video/mp4", filename=os.path.basename(latest))
    path = os.path.abspath("stitched_output.mp4")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No stitched file found")
    return FileResponse(path, media_type="video/mp4", filename="stitched_output.mp4")


@app.get("/api/stitched/{name}")
def get_stitched_named(name: str, user: Dict = Depends(verify_firebase_token)):
    if not name.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    base_dir = os.getenv("CLIPS_DIR") or os.path.join(os.path.abspath(os.getcwd()), "clips")
    namespace = _user_namespace(user) or ""
    search_dirs = []
    if namespace:
        search_dirs.append(os.path.join(base_dir, *(namespace.split("/")), "stitched"))
    search_dirs.append(os.path.join(base_dir, "stitched"))
    for d in search_dirs:
        path = os.path.join(d, name)
        if os.path.isfile(path):
            return FileResponse(path, media_type="video/mp4", filename=name)
    raise HTTPException(status_code=404, detail="Stitched file not found")


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


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    user: Dict = Depends(verify_firebase_token),
):
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
        try:
            result = service.openai_client.transcribe(tmp_path)
        except Exception as exc:
            return JSONResponse({"success": False, "error": str(exc)})
        text = (result or {}).get("text", "")
        return JSONResponse({"success": True, "text": text, "length": len(text)})
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


# Optionally mount Gradio UI at /gradio for transition
try:
    import gradio as gr  # type: ignore
    from ..webui.app import app as gradio_blocks

    app = gr.mount_gradio_app(app, gradio_blocks, path="/gradio")
except Exception:
    pass


def _mount_static(app_: FastAPI) -> None:
    try:
        web_dist = os.path.abspath(os.path.join(os.getcwd(), "web", "dist"))
        if os.path.isdir(web_dist) and os.listdir(web_dist):
            app_.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    except Exception:
        pass


# --- Interior Timelapse ---

@app.get("/api/timelapse/options")
def timelapse_options():
    return JSONResponse(get_all_options())


@app.post("/api/generate/timelapse")
async def generate_timelapse(request: Request, user: Dict = Depends(verify_firebase_token)):
    from ..utils.job_manager import create_job, update_job, start_job

    _check_usage_or_401(user)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    room_type = (body.get("room_type") or "").strip()
    style = (body.get("style") or "").strip()
    if not room_type or not style:
        raise HTTPException(status_code=400, detail="room_type and style are required")

    features = body.get("features") or []
    if isinstance(features, str):
        features = [f.strip() for f in features.split(",") if f.strip()]

    materials = body.get("materials") or []
    if isinstance(materials, str):
        materials = [m.strip() for m in materials.split(",") if m.strip()]

    req = TimelapseRequest(
        room_type=room_type,
        style=style,
        features=features,
        materials=materials,
        lighting=(body.get("lighting") or "natural").strip(),
        duration=8,
        camera_motion=(body.get("camera_motion") or "slow_pan").strip(),
        progression=(body.get("progression") or "construction").strip(),
        freeform_description=(body.get("freeform_description") or "").strip(),
    )

    stop_after = body.get("stop_after")
    resume_state = body.get("resume_state")

    video_model = body.get("video_model", "cheap")
    if video_model not in ("cheap", "expensive"):
        video_model = "cheap"

    try:
        num_stages = int(body.get("num_stages", 7))
    except (TypeError, ValueError):
        num_stages = 7
    num_stages = max(2, min(num_stages, 7))

    job_id = create_job()
    # Track which user owns this job so we can count usage on completion.
    update_job(job_id, uid=user["uid"], is_anonymous=user["is_anonymous"])

    def on_progress(phase, step, total, message, partial_result=None):
        updates = {"phase": phase, "step": step, "total_steps": total, "message": message}
        if partial_result is not None:
            updates["partial_result"] = partial_result
        update_job(job_id, **updates)

    start_job(
        job_id,
        service.generate_timelapse_v2,
        req,
        stop_after=stop_after,
        resume_state=resume_state,
        on_progress=on_progress,
        video_model=video_model,
        num_stages=num_stages,
    )

    return JSONResponse({"job_id": job_id})


@app.post("/api/generate/custom-videos")
async def generate_custom_videos(request: Request, user: Dict = Depends(verify_firebase_token)):
    from ..utils.job_manager import create_job, update_job, start_job

    _check_usage_or_401(user)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    image_urls = body.get("image_urls") or []
    if not isinstance(image_urls, list) or len(image_urls) < 2:
        raise HTTPException(status_code=400, detail="At least 2 image_urls are required")

    for url in image_urls:
        if not isinstance(url, str) or not url.startswith("http"):
            raise HTTPException(status_code=400, detail="All image_urls must be valid HTTP URLs")

    model = body.get("model", "cheap")
    if model not in ("cheap", "expensive"):
        raise HTTPException(status_code=400, detail="model must be 'cheap' or 'expensive'")

    stop_after = body.get("stop_after")
    resume_state = body.get("resume_state")

    job_id = create_job()
    update_job(job_id, uid=user["uid"], is_anonymous=user["is_anonymous"])

    def on_progress(phase, step, total, message, partial_result=None):
        updates = {"phase": phase, "step": step, "total_steps": total, "message": message}
        if partial_result is not None:
            updates["partial_result"] = partial_result
        update_job(job_id, **updates)

    start_job(
        job_id,
        service.generate_custom_videos,
        image_urls=image_urls,
        model=model,
        stop_after=stop_after,
        resume_state=resume_state,
        on_progress=on_progress,
    )

    return JSONResponse({"job_id": job_id})


@app.post("/api/generate/stitch-custom")
async def stitch_custom_videos(request: Request, user: Dict = Depends(verify_firebase_token)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    video_urls = body.get("video_urls") or []
    if not isinstance(video_urls, list) or len(video_urls) < 1:
        raise HTTPException(status_code=400, detail="At least 1 video URL is required")

    for url in video_urls:
        if not isinstance(url, str) or not url.startswith("http"):
            raise HTTPException(status_code=400, detail="All video_urls must be valid HTTP URLs")

    result = stitch_timelapse_clips(
        video_sources=video_urls, speed=1.5, dissolve=False, hold_first_frame=0.0,
    )

    if result.get("success") and result.get("output_path"):
        out_path = result["output_path"]
        namespace = _user_namespace(user) or ""
        base_dir = os.getenv("CLIPS_DIR") or os.path.join(os.path.abspath(os.getcwd()), "clips")
        target_dir = os.path.join(base_dir, *(namespace.split("/") if namespace else []), "stitched")
        os.makedirs(target_dir, exist_ok=True)
        fname = f"stitched-{int(time.time())}.mp4"
        dest = os.path.join(target_dir, fname)
        try:
            shutil.copyfile(out_path, dest)
            result["stitched_url"] = f"/api/stitched/{fname}"
        except Exception as exc:
            result.setdefault("error", str(exc))

    return JSONResponse(result)


def _maybe_count_job_usage(job: Dict, job_id: str) -> None:
    """If the job just completed with a video_url and belongs to an anon user, count it once."""
    from ..utils.job_manager import update_job

    if job.get("status") != "completed" or job.get("usage_counted"):
        return
    result = job.get("result") or {}
    if not result.get("video_url"):
        return
    uid = job.get("uid")
    is_anonymous = job.get("is_anonymous")
    if uid and is_anonymous:
        _inc_usage({"uid": uid, "is_anonymous": True})
    update_job(job_id, usage_counted=True)


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, user: Dict = Depends(verify_firebase_token)):
    from ..utils.job_manager import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    _maybe_count_job_usage(job, job_id)

    job.pop("created_at", None)
    job.pop("usage_counted", None)
    job.pop("uid", None)
    job.pop("is_anonymous", None)
    return JSONResponse(job)


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_sse(request: Request, job_id: str, user: Dict = Depends(verify_firebase_token)):
    """Stream job progress as Server-Sent Events."""
    import asyncio
    from ..utils.job_manager import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_key = None
        heartbeat_counter = 0
        while True:
            if await request.is_disconnected():
                break

            job = get_job(job_id)
            if not job:
                yield f"data: {json.dumps({'status': 'failed', 'message': 'Job expired'})}\n\n"
                break

            state_key = (job["status"], job.get("phase"), job.get("step"), job.get("message"))
            if state_key == last_key:
                heartbeat_counter += 1
                if heartbeat_counter >= 20:  # ~10s
                    event = {
                        "status": job["status"],
                        "phase": job.get("phase"),
                        "step": job.get("step", 0),
                        "total_steps": job.get("total_steps", 0),
                        "message": job.get("message", ""),
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    heartbeat_counter = 0
                await asyncio.sleep(0.5)
                continue
            last_key = state_key
            heartbeat_counter = 0

            event = {
                "status": job["status"],
                "phase": job.get("phase"),
                "step": job.get("step", 0),
                "total_steps": job.get("total_steps", 0),
                "message": job.get("message", ""),
                "partial_result": job.get("partial_result"),
            }

            if job["status"] == "completed":
                event["result"] = job.get("result")
                _maybe_count_job_usage(job, job_id)

            if job["status"] == "failed":
                event["error"] = (job.get("result") or {}).get("error", job.get("message", ""))

            yield f"data: {json.dumps(event)}\n\n"

            if job["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/debug/fake-job")
def create_fake_job():
    """Create a simulated job for testing SSE plumbing without AI costs."""
    import time
    from ..utils.job_manager import create_job, update_job, start_job

    job_id = create_job()

    def fake_worker():
        phases = [
            ("plan", 1, 1, "Generating scene bible..."),
            ("stage_1", 1, 2, "Stage 1: generating initial image..."),
            ("stage_1", 2, 2, "Stage 1 complete"),
            ("stage_2", 1, 2, "Stage 2: GPT planning next edit..."),
            ("stage_2", 2, 2, "Stage 2 complete"),
            ("stage_3", 1, 2, "Stage 3: generating edited image..."),
            ("stage_3", 2, 2, "Stage 3 complete"),
            ("video_1", 1, 1, "Generating transition 1 of 2"),
            ("video_2", 1, 1, "Generating transition 2 of 2"),
            ("stitch", 1, 1, "Stitching videos..."),
        ]
        for phase, step, total, msg in phases:
            update_job(job_id, phase=phase, step=step, total_steps=total, message=msg)
            time.sleep(2)
        return {
            "success": True,
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "stitched_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        }

    start_job(job_id, fake_worker)
    return JSONResponse({"job_id": job_id})


def _run_image_edit_diagnostic() -> Dict[str, Any]:
    """Time Nano Banana Pro T2I and Edit calls end-to-end from inside the deployed container."""
    import time
    import socket
    import ssl
    import json as _json
    from urllib.parse import urlparse
    import requests as _req

    api_url = "https://api.aimlapi.com/v1/images/generations"
    fallback_cdn_image_url = "https://cdn.aimlapi.com/generations/openai-image-generation/1775871436710-f17de23b-4eb6-4b28-b9ed-441c937706c1.png"

    settings = get_settings()
    auth_headers = {
        "Authorization": f"Bearer {settings.aimlapi_api_key}",
        "Content-Type": "application/json",
    }

    result: Dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "api_url": api_url,
    }
    logger.info("[DEBUG time-image-edit] starting run at %s", result["started_at"])

    def _headers_dict(resp) -> Dict[str, str]:
        try:
            return {k: v for k, v in resp.headers.items()}
        except Exception:
            return {}

    def _extract_image_url(data: Any) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        items = data.get("data") or data.get("images") or data.get("results") or []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    u = item.get("url") or item.get("image_url") or item.get("uri")
                    if isinstance(u, str) and u.startswith("http"):
                        return u
                elif isinstance(item, str) and item.startswith("http"):
                    return item
        u = data.get("url") or data.get("image_url")
        if isinstance(u, str) and u.startswith("http"):
            return u
        return None

    def _post_probe(label: str, body: Dict[str, Any]):
        probe: Dict[str, Any] = {
            "model": body.get("model"),
            "request_body_bytes": len(_json.dumps(body).encode("utf-8")),
        }
        logger.info("[DEBUG time-image-edit] %s: starting POST model=%s", label, body.get("model"))
        session = _req.Session()
        raw_data: Any = None
        t0 = time.time()
        try:
            resp = session.post(api_url, json=body, headers=auth_headers, timeout=(10, 600), stream=True)
            t_headers = time.time()
            content = resp.content
            t_body = time.time()
            try:
                data = resp.json()
                raw_data = data
            except Exception:
                data = {"error_text": resp.text[:500]}
            probe.update({
                "status_code": resp.status_code,
                "total_ms": int((t_body - t0) * 1000),
                "time_to_headers_ms": int((t_headers - t0) * 1000),
                "body_download_ms": int((t_body - t_headers) * 1000),
                "response_body_bytes": len(content),
                "response_headers": _headers_dict(resp),
                "response_preview": str(data)[:500],
            })
        except _req.Timeout as e:
            probe.update({"error": f"timeout: {e}", "total_ms": int((time.time() - t0) * 1000)})
        except _req.RequestException as e:
            probe.update({"error": f"request_error: {e}", "total_ms": int((time.time() - t0) * 1000)})
        logger.info("[DEBUG time-image-edit] %s: done %s", label, _json.dumps(probe)[:1500])
        return probe, raw_data

    parsed = urlparse(api_url)
    host = parsed.hostname or "api.aimlapi.com"
    port = parsed.port or 443
    socket_probe: Dict[str, Any] = {"host": host, "port": port}
    try:
        t_dns_0 = time.time()
        ip = socket.gethostbyname(host)
        t_dns_1 = time.time()
        socket_probe["dns_ms"] = int((t_dns_1 - t_dns_0) * 1000)
        socket_probe["resolved_ip"] = ip

        t_tcp_0 = time.time()
        sock = socket.create_connection((ip, port), timeout=10)
        t_tcp_1 = time.time()
        socket_probe["tcp_connect_ms"] = int((t_tcp_1 - t_tcp_0) * 1000)

        t_tls_0 = time.time()
        context = ssl.create_default_context()
        ssock = context.wrap_socket(sock, server_hostname=host)
        t_tls_1 = time.time()
        socket_probe["tls_handshake_ms"] = int((t_tls_1 - t_tls_0) * 1000)
        try:
            ssock.close()
        except Exception:
            pass
    except Exception as e:
        socket_probe["error"] = f"{type(e).__name__}: {e}"
    result["socket_probe"] = socket_probe
    logger.info("[DEBUG time-image-edit] socket_probe: %s", _json.dumps(socket_probe))

    cdn_probe: Dict[str, Any] = {"url": fallback_cdn_image_url}
    t0 = time.time()
    try:
        cdn_resp = _req.get(fallback_cdn_image_url, timeout=(10, 60), stream=True)
        t_headers = time.time()
        cdn_bytes = cdn_resp.content
        t_body = time.time()
        cdn_probe.update({
            "status_code": cdn_resp.status_code,
            "total_ms": int((t_body - t0) * 1000),
            "time_to_headers_ms": int((t_headers - t0) * 1000),
            "body_download_ms": int((t_body - t_headers) * 1000),
            "bytes": len(cdn_bytes),
            "response_headers": _headers_dict(cdn_resp),
        })
    except Exception as e:
        cdn_probe.update({"error": f"{type(e).__name__}: {e}", "total_ms": int((time.time() - t0) * 1000)})
    result["cdn_fetch_probe"] = cdn_probe
    logger.info("[DEBUG time-image-edit] cdn_fetch_probe: %s", _json.dumps({k: v for k, v in cdn_probe.items() if k != "response_headers"}))

    t2i_probe, t2i_raw = _post_probe("t2i", {
        "model": "google/nano-banana-pro",
        "prompt": "A modern luxury patio, natural daylight, photoreal, 24mm wide.",
        "aspect_ratio": "16:9",
        "resolution": "1K",
        "num_images": 1,
    })
    result["t2i_probe"] = t2i_probe

    fresh_url = _extract_image_url(t2i_raw)
    i2i_source_url = fresh_url or fallback_cdn_image_url
    i2i_source_is_fresh = fresh_url is not None
    logger.info(
        "[DEBUG time-image-edit] i2i source_url=%s (fresh_from_t2i=%s)",
        i2i_source_url, i2i_source_is_fresh,
    )

    i2i_probe, _i2i_raw = _post_probe("i2i", {
        "model": "google/nano-banana-pro-edit",
        "prompt": "Make the walls warm off-white matte. Change nothing else.",
        "image_urls": [i2i_source_url],
        "aspect_ratio": "16:9",
        "resolution": "1K",
        "num_images": 1,
    })
    i2i_probe["source_image_url"] = i2i_source_url
    i2i_probe["source_is_fresh_t2i_output"] = i2i_source_is_fresh
    result["i2i_probe"] = i2i_probe

    logger.info("[DEBUG time-image-edit] FINAL socket=%sms cdn=%sms t2i=%sms i2i=%sms",
                socket_probe.get("tls_handshake_ms"),
                cdn_probe.get("total_ms"),
                result["t2i_probe"].get("total_ms"),
                result["i2i_probe"].get("total_ms"))
    return result


@app.get("/api/debug/time-image-edit")
def debug_time_image_edit():
    return JSONResponse(_run_image_edit_diagnostic())


@app.on_event("startup")
def _maybe_run_startup_diagnostic():
    if os.getenv("RUN_STARTUP_DIAGNOSTIC") != "1":
        return
    import threading
    def _runner():
        try:
            _run_image_edit_diagnostic()
        except Exception as e:
            logger.exception("[DEBUG time-image-edit] startup diagnostic crashed: %s", e)
    logger.info("[DEBUG time-image-edit] RUN_STARTUP_DIAGNOSTIC=1 — spawning background diagnostic thread")
    threading.Thread(target=_runner, daemon=True, name="startup-diagnostic").start()


# --- Speech to Video (MVP) ---
@app.post("/api/generate/speech-to-video")
async def create_speech_to_video(
    prompt: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    model: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    user: Dict = Depends(verify_firebase_token),
):
    _check_usage_or_401(user)

    text = (prompt or "").strip()
    tmp_path = None
    if not text and audio:
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
            transcript = service.openai_client.transcribe(tmp_path)
            text = (transcript or {}).get("text", "").strip()
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    if not text:
        raise HTTPException(status_code=400, detail="prompt_or_audio_required")

    from ..utils.job_manager import create_job, update_job, start_job

    job_id = create_job()
    update_job(job_id, uid=user["uid"], is_anonymous=user["is_anonymous"])

    def on_progress(phase, step, total, message, partial_result=None):
        updates = {"phase": phase, "step": step, "total_steps": total, "message": message}
        if partial_result is not None:
            updates["partial_result"] = partial_result
        update_job(job_id, **updates)

    def run():
        update_job(job_id, phase="generating", step=1, total_steps=1, message="Generating video...")
        return service.generate_speech_to_video(text, model=model, duration=duration)

    start_job(job_id, run)

    return JSONResponse({"job_id": job_id})

_mount_static(app)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("src.speech_to_video.api.server:app", host=host, port=port, reload=os.getenv("RELOAD", "0") in {"1", "true", "on", "yes"})
