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
from ..utils.clip_store import add_clip, list_clips, clear_clips, reorder_clips, remove_stitched_clips, remove_clip, get_response, delete_namespace
from ..utils import credit_store
from ..utils.video import stitch_videos_detailed, stitch_timelapse_clips
from . import credits as credits_api
from . import legal as legal_api
from .firebase_auth import verify_firebase_token


settings = get_settings()
service = VideoService(settings)

app = FastAPI(title="Speech to Video API")
app.include_router(credits_api.router)
app.include_router(legal_api.router)


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


# --------- Auth and credit gating (Firebase ID token + Firestore ledger) ---------

# Credit cost per (model_family, duration_seconds). V1 ships single
# model + single duration (Session 52). Hailuo 6s and all Kling SKUs were
# dropped — mobile no longer sends a picker. Kept as a dict so future
# variants slot back in without restructuring callers.
CREDIT_COSTS: Dict[tuple, int] = {
    ("hailuo", 10): 100,  # S87 redenomination ×10 (legacy S2V path, paused; was 10)
}

_ANON_STARTER_CREDITS = 500  # S87 redenomination (100 coins=$1): covers exactly one flat-priced template gen (500 cr) so anons get one free


def _cost_table_public() -> Dict[str, Dict[str, int]]:
    """Shape CREDIT_COSTS into {family: {duration_str: cost}} for the mobile client."""
    out: Dict[str, Dict[str, int]] = {}
    for (family, dur), cost in CREDIT_COSTS.items():
        out.setdefault(family, {})[str(dur)] = int(cost)
    return out


def _model_family(model_id: Optional[str]) -> Optional[str]:
    """V1 ships Hailuo only. Kling branch removed Session 52."""
    if not model_id:
        return None
    m = model_id.lower()
    if "hailuo" in m or "minimax" in m:
        return "hailuo"
    return None


def _cost_for(model_id: Optional[str], duration: Optional[int]) -> Optional[int]:
    family = _model_family(model_id)
    if family is None or duration is None:
        return None
    return CREDIT_COSTS.get((family, int(duration)))


def _ensure_ledger(user: Dict) -> None:
    """Seed the anon starter once per anon UID. No-op for signed-in users and on replay."""
    if user.get("is_anonymous"):
        try:
            credit_store.ensure_anon_starter(user["uid"], amount=_ANON_STARTER_CREDITS)
        except Exception:
            logger.exception("ensure_anon_starter failed uid=%s", user.get("uid"))


def _check_credits_or_402(user: Dict, cost: int) -> int:
    """Raise 402 if balance < cost. Returns current balance on success."""
    _ensure_ledger(user)
    balance = credit_store.get_balance(user["uid"])
    if balance < int(cost):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "insufficient_credits",
                "required": int(cost),
                "balance": int(balance),
            },
        )
    return balance


def _user_namespace(user: Dict) -> Optional[str]:
    """Build clip-store namespace: env-prefix / firebase-uid."""
    ns = os.getenv("CLIPS_NAMESPACE", "")
    uid = user["uid"]
    return "/".join([p for p in [ns, uid] if p]) or None


@app.get("/api/auth/session")
def auth_session(user: Dict = Depends(verify_firebase_token)):
    _ensure_ledger(user)
    balance = credit_store.get_balance(user["uid"])
    return {
        "uid": user["uid"],
        "is_anonymous": user["is_anonymous"],
        "email": user.get("email"),
        "name": user.get("name"),
        "provider": user.get("provider"),
        "credit_balance": int(balance),
        "cost_table": _cost_table_public(),
    }


@app.delete("/api/account")
def delete_account(user: Dict = Depends(verify_firebase_token)):
    """Permanently delete the caller's account. Required by App Store 5.1.1(v).

    Three independent, idempotent steps: credits ledger, clip namespace,
    Firebase user. A failure in one step is logged but does not prevent the
    others — on retry each already-completed step is a no-op.
    """
    import firebase_admin
    from firebase_admin import auth as fb_auth

    uid = user["uid"]
    namespace = _user_namespace(user)
    deleted = {"credits": False, "clips": False, "firebase_user": False}

    try:
        deleted["credits"] = bool(credit_store.delete_ledger(uid))
    except Exception:
        logger.exception("delete_account: credits ledger delete failed uid=%s", uid)

    if namespace:
        try:
            deleted["clips"] = bool(delete_namespace(namespace))
        except Exception:
            logger.exception("delete_account: clip namespace delete failed uid=%s ns=%s", uid, namespace)

    # Firebase user deletion is the canonical App Store requirement; must succeed
    # or the retry loop can fix everything else later.
    try:
        fb_auth.delete_user(uid)
        deleted["firebase_user"] = True
    except fb_auth.UserNotFoundError:
        deleted["firebase_user"] = True  # already gone — treat as success
    except Exception as exc:
        logger.exception("delete_account: firebase user delete failed uid=%s", uid)
        raise HTTPException(status_code=500, detail=f"firebase_delete_failed: {exc}")

    logger.info("account deleted uid=%s result=%s", uid, deleted)
    return JSONResponse({"success": True, "deleted": deleted})


@app.post("/api/generate")
def generate_video(
    prompt: str = Form(...),
    duration: int = Form(10),
    quality: str = Form("high"),
    user: Dict = Depends(verify_firebase_token),
):
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


def _maybe_consume_job_credits(job: Dict, job_id: str) -> None:
    """Deduct the job's credit cost from its owner — exactly once per job.

    Runs only after the job has successfully produced a video_url, so failed
    generations don't consume credits. `try_claim` gives us atomic
    exactly-once semantics across concurrent pollers.
    """
    from ..utils.job_manager import try_claim

    if job.get("status") != "completed":
        return
    result = job.get("result") or {}
    if not result.get("video_url"):
        return
    if not try_claim(job_id, "credit_consumed"):
        return
    uid = job.get("uid")
    cost = int(job.get("credit_cost") or 0)
    if not uid or cost <= 0:
        return
    try:
        new_balance = credit_store.consume(uid, cost)
        logger.info(
            "credits consumed uid=%s job=%s cost=%s new_balance=%s",
            uid, job_id, cost, new_balance,
        )
    except credit_store.InsufficientCredits as exc:
        logger.error(
            "credits consume shortfall at completion uid=%s job=%s: %s",
            uid, job_id, exc,
        )
    except Exception:
        logger.exception("credits consume failed uid=%s job=%s", uid, job_id)


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, user: Dict = Depends(verify_firebase_token)):
    from ..utils.job_manager import get_job

    job = get_job(job_id)
    if not job:
        # AIV-78: user-side observation of an orphaned job (likely from a
        # container restart between submit and poll). Grep `JOB_POLL_MISS`
        # in prod logs to measure orphan rate before deciding on full
        # Firestore-backed durability.
        logger.warning(
            "JOB_POLL_MISS job_id=%s uid=%s anon=%s",
            job_id, user.get("uid"), user.get("is_anonymous"),
        )
        raise HTTPException(status_code=404, detail="Job not found")

    _maybe_consume_job_credits(job, job_id)

    for internal_field in ("created_at", "uid", "is_anonymous", "credit_cost", "credit_consumed", "usage_counted"):
        job.pop(internal_field, None)
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
                _maybe_consume_job_credits(job, job_id)

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


# AIV-80: long-thread durability harness.
#
# Acceptance: submit a 7-8min job on Replit prod and verify the worker thread
# survives + poll calls keep returning 200. Today Pipeline B can't be run end-
# to-end (no real scene-image assets — gated on AIV-84 #1), so this harness
# exercises the SAME job_manager.start_job / update_job / get_job code path
# at zero API spend by sleeping + logging every 30s for N seconds.
#
# Gated by ENABLE_LONG_JOB_TEST=1 (Replit Deployment Secrets) to keep the
# endpoint dormant in normal prod. No auth — env-gated.
#
# Replit prod procedure:
#   1. Set ENABLE_LONG_JOB_TEST=1 in Replit Deployment Secrets; redeploy.
#   2. JOB=$(curl -sX POST 'https://speech-2-video.ai/api/debug/long-job?duration_s=480' | jq -r .job_id)
#   3. while :; do curl -s "https://speech-2-video.ai/api/debug/long-job/$JOB" | jq -c .; sleep 30; done
#   4. After ~8 min, expect status=completed with no intermediate 502/504/timeouts.
#   5. Unset ENABLE_LONG_JOB_TEST + redeploy when done.
@app.post("/api/debug/long-job")
def debug_long_job_start(duration_s: int = 480):
    if os.getenv("ENABLE_LONG_JOB_TEST") != "1":
        raise HTTPException(status_code=404, detail="disabled")
    if not (30 <= duration_s <= 900):
        raise HTTPException(status_code=400, detail="duration_s must be 30..900")
    from ..utils.job_manager import create_job, start_job, update_job

    job_id = create_job()
    tick_s = 10 if duration_s <= 120 else 30
    steps = max(1, duration_s // tick_s)

    def _aiv80_worker():
        for i in range(steps):
            time.sleep(tick_s)
            elapsed = (i + 1) * tick_s
            update_job(
                job_id,
                phase="sleeping",
                step=i + 1,
                total_steps=steps,
                message=f"AIV-80 fake worker {elapsed}s / {duration_s}s",
            )
            logger.info("AIV-80 long-job %s tick step=%d/%d", job_id, i + 1, steps)
        return {"success": True, "duration_s": duration_s, "video_url": "debug://aiv-80"}

    start_job(job_id, _aiv80_worker)
    logger.info("AIV-80 long-job %s started duration_s=%d tick_s=%d", job_id, duration_s, tick_s)
    return {
        "job_id": job_id,
        "poll_url": f"/api/debug/long-job/{job_id}",
        "duration_s": duration_s,
        "tick_s": tick_s,
    }


@app.get("/api/debug/long-job/{job_id}")
def debug_long_job_poll(job_id: str):
    if os.getenv("ENABLE_LONG_JOB_TEST") != "1":
        raise HTTPException(status_code=404, detail="disabled")
    from ..utils.job_manager import get_job

    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "status": job.get("status"),
        "phase": job.get("phase"),
        "step": job.get("step"),
        "total_steps": job.get("total_steps"),
        "message": job.get("message"),
        "result": job.get("result"),
    }


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


# --- AIV-78 observability: measure orphan rate without persisting state ---
@app.on_event("startup")
def _log_job_manager_startup():
    """Fresh-container marker. Pair with JOB_ORPHAN_SNAPSHOT and JOB_POLL_MISS
    to triangulate post-restart orphans in Replit logs."""
    logger.info("JOB_MANAGER_STARTUP pid=%s time=%s", os.getpid(), int(time.time()))


@app.on_event("shutdown")
def _log_job_orphan_snapshot():
    """List in-flight jobs at the moment uvicorn begins shutdown. Hard kills
    (SIGKILL from Replit) won't fire this; that case is caught by the
    next-startup JOB_MANAGER_STARTUP log + subsequent JOB_POLL_MISS lines."""
    try:
        from ..utils.job_manager import inflight_jobs
        items = inflight_jobs()
        if not items:
            logger.info("JOB_ORPHAN_SNAPSHOT count=0")
            return
        # One line per job — grep-friendly, and each line stays readable.
        logger.warning("JOB_ORPHAN_SNAPSHOT count=%d", len(items))
        for it in items:
            logger.warning(
                "JOB_ORPHAN job_id=%s uid=%s status=%s phase=%s cost=%s anon=%s age_s=%s",
                it["job_id"], it["uid"], it["status"], it["phase"],
                it["credit_cost"], it["is_anonymous"], it["age_s"],
            )
    except Exception as e:  # noqa: BLE001
        logger.exception("JOB_ORPHAN_SNAPSHOT failed: %s", e)


# --- Speech to Video (MVP) ---
@app.post("/api/generate/speech-to-video")
async def create_speech_to_video(
    prompt: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    model: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    user: Dict = Depends(verify_firebase_token),
):
    cost = _cost_for(model, duration)
    if cost is None:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported_model_or_duration: model={model!r} duration={duration!r}",
        )
    _check_credits_or_402(user, cost)

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

    from ..utils.job_manager import try_create_credit_job, update_job, start_job

    # Atomic gate: at most one unsettled credit-bearing job per uid. Closes the
    # TOCTOU race between _check_credits_or_402 (read) and consume (write at
    # completion) — concurrent submits with the same balance would otherwise
    # all pass the eager check and only the first deduction would succeed.
    job_id = try_create_credit_job(
        uid=user["uid"],
        credit_cost=int(cost),
        is_anonymous=bool(user["is_anonymous"]),
    )
    if not job_id:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "concurrent_job_in_flight",
                "message": "A generation is already in progress for this account.",
            },
        )

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

# ----------------------------------------------------------------------
# V2 generate template-video endpoint (AIV-15). Dispatcher in AIV-14.
# ----------------------------------------------------------------------
# JSON body, not Form, since the payload is structured. Selfie was uploaded
# via /api/upload/selfie ahead of this call (AIV-89). credit_cost lives in
# the template registry doc per AIV-36 — not in CREDIT_COSTS table.

from pydantic import BaseModel


class TemplateVideoRequest(BaseModel):
    template_id: str
    selfie_key: str
    prompt_overrides: Optional[Dict[str, Any]] = None


@app.post("/api/generate/template-video")
def create_template_video(
    req: TemplateVideoRequest,
    user: Dict = Depends(verify_firebase_token),
):
    from ..utils import template_registry
    from ..utils.job_manager import try_create_credit_job, update_job, start_job

    # 1. Pre-load template — 404 fast if missing (don't burn a job slot for typos).
    try:
        template = template_registry.get_template(req.template_id)
    except template_registry.TemplateNotFound:
        raise HTTPException(status_code=404, detail=f"template_not_found: {req.template_id}")

    credit_cost = template.get("credit_cost")
    if not isinstance(credit_cost, int) or credit_cost <= 0:
        raise HTTPException(
            status_code=500,
            detail=f"template_missing_credit_cost: {req.template_id}",
        )

    # 2. Validate selfie_key belongs to the caller. Rejects cross-uid attempts
    # without ever touching R2.
    expected_prefix = f"selfies/{user['uid']}/"
    if not req.selfie_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="selfie_key does not belong to current user")

    # 3. Eager 402 — fast surface to mobile so the paywall can open before we
    # bother creating an atomic job slot.
    _check_credits_or_402(user, credit_cost)

    # 4. Atomic concurrent-submit gate (TOCTOU close vs the eager check above).
    job_id = try_create_credit_job(
        uid=user["uid"],
        credit_cost=int(credit_cost),
        is_anonymous=bool(user["is_anonymous"]),
    )
    if not job_id:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "concurrent_job_in_flight",
                "message": "A generation is already in progress for this account.",
            },
        )

    # 5. Worker. Adapter normalizes the dispatcher's (phase, template_id)
    # callback shape to job_manager's (phase, message, ...) shape.
    def on_progress(phase=None, template_id=None, **_extra):
        update_job(job_id, phase=phase or "running", message=phase or "")

    def run():
        return service.generate_template_video(
            template_id=req.template_id,
            selfie_key=req.selfie_key,
            prompt_overrides=req.prompt_overrides,
            on_progress=on_progress,
            uid=user["uid"],
            job_id=job_id,
        )

    start_job(job_id, run)
    return JSONResponse({"job_id": job_id})


# ----------------------------------------------------------------------
# V2 GET /api/templates (AIV-83). Public read endpoint for the mobile carousel.
# ----------------------------------------------------------------------
# Always filters to published_status="published". Admin scripts call
# `template_registry.list_templates(published_only=False)` directly when they
# need drafts.
#
# Caching: ~25 docs at launch — list_templates() is cheap, but we still cache
# in-process for 60s to keep cold-start cost off the carousel and to serve a
# stable ETag for mobile's If-None-Match. ETag is weak: sha256 prefix of
# sorted `id|updated_at`.
#
# No CDN cache + no pagination at launch. Both can land if catalog growth or
# carousel latency demand it.

import hashlib as _hashlib
import threading as _threading

from fastapi.responses import Response as _Response

_TEMPLATE_CACHE_TTL_SEC = 60
_template_cache_lock = _threading.Lock()
_template_cache: Dict[str, Any] = {"ts": 0.0, "templates": None, "etag": None}


def _serialize_template(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(doc)
    for k in ("created_at", "updated_at"):
        v = out.get(k)
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
    return out


def _compute_template_etag(serialized: List[Dict[str, Any]]) -> str:
    parts = sorted(
        f"{t.get('id', '')}|{t.get('updated_at', '')}" for t in serialized
    )
    digest = _hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return f'W/"{digest[:16]}"'


def _get_published_templates_cached():
    # Lock held through the Firestore fetch to prevent stampede; ~25 docs +
    # fast read make serial fetches a non-issue.
    with _template_cache_lock:
        now = time.time()
        cached = _template_cache["templates"]
        if cached is not None and (now - _template_cache["ts"]) < _TEMPLATE_CACHE_TTL_SEC:
            return cached, _template_cache["etag"]

        from ..utils import template_registry
        raw = template_registry.list_templates(published_only=True)
        serialized = [_serialize_template(t) for t in raw]
        etag = _compute_template_etag(serialized)
        _template_cache["ts"] = now
        _template_cache["templates"] = serialized
        _template_cache["etag"] = etag
        return serialized, etag


@app.get("/api/templates")
def list_published_templates(request: Request):
    templates, etag = _get_published_templates_cached()
    inm = request.headers.get("if-none-match", "")
    if inm and inm == etag:
        return _Response(status_code=304, headers={"ETag": etag})
    return JSONResponse(
        {"templates": templates},
        headers={"ETag": etag, "Cache-Control": "public, max-age=60"},
    )


# ----------------------------------------------------------------------
# V2 selfie endpoints (AIV-89). Policy locked in AIV-77.
# ----------------------------------------------------------------------
# Selfies live in the private R2 selfies bucket under `selfies/{uid}/`.
# Server enforces uid prefix on every read/delete. Inputs are also deleted
# inline once a gen is terminal (video_service._dispatch_motion_transfer); the
# R2 backstop is a 1-day expiry lifecycle on selfies/, nbp-regen/, composites/
# set via scripts/set_r2_selfie_lifecycle.py. (The old "30d on selfies/" comment
# was wrong — that rule was never actually present in the bucket; verified S85.)
# See AIV-89.

import secrets as _secrets
from datetime import datetime as _dt, timedelta as _td

from ..utils import r2_client as _r2

_SELFIE_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_SELFIE_EXT_MAP = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def _selfie_ext_for(content_type: str) -> str:
    return _SELFIE_EXT_MAP.get((content_type or "").lower(), ".bin")


def _selfies_prefix(uid: str) -> str:
    return f"selfies/{uid}/"


@app.post("/api/upload/selfie")
async def upload_selfie(
    file: UploadFile = File(...),
    user: Dict = Depends(verify_firebase_token),
):
    ct = file.content_type or ""
    if not ct.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"content_type must be image/*; got {ct!r}")

    body = await file.read()
    try:
        await file.close()
    except Exception:
        pass

    if len(body) > _SELFIE_MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"selfie size {len(body)} exceeds limit {_SELFIE_MAX_BYTES}")
    if not body:
        raise HTTPException(status_code=400, detail="empty file")

    uid = user["uid"]
    epoch_ms = int(time.time() * 1000)
    rand6 = _secrets.token_hex(3)
    key = f"{_selfies_prefix(uid)}{epoch_ms}_{rand6}{_selfie_ext_for(ct)}"

    try:
        _r2.upload_bytes(
            body, key,
            content_type=ct,
            bucket=settings.r2_selfies_bucket,
            cache_control="private, max-age=86400",
        )
    except _r2.R2NotConfigured as exc:
        raise HTTPException(status_code=500, detail=f"r2_not_configured: {exc}")
    except Exception as exc:
        logger.exception("Selfie upload to R2 failed")
        raise HTTPException(status_code=500, detail=f"upload_failed: {exc}")

    # Upper bound only — the R2 lifecycle backstop expires inputs after 1 day,
    # and the inline purge usually removes them within minutes of the gen.
    expires_at = (_dt.utcnow() + _td(days=1)).replace(microsecond=0).isoformat() + "Z"
    return {"key": key, "expires_at": expires_at, "size_bytes": len(body)}


@app.get("/api/selfies")
def list_selfies(user: Dict = Depends(verify_firebase_token)):
    uid = user["uid"]
    try:
        objects = _r2.list_objects(_selfies_prefix(uid), bucket=settings.r2_selfies_bucket)
    except _r2.R2NotConfigured as exc:
        raise HTTPException(status_code=500, detail=f"r2_not_configured: {exc}")

    out = []
    for obj in objects:
        last_mod = obj.get("LastModified")
        out.append({
            "key": obj["Key"],
            "uploaded_at": last_mod.isoformat() if hasattr(last_mod, "isoformat") else None,
            "size_bytes": obj.get("Size"),
        })
    return out


@app.delete("/api/selfies")
def delete_all_or_one_selfie(
    key: Optional[str] = None,
    user: Dict = Depends(verify_firebase_token),
):
    """Delete either one selfie (when ?key=... is provided) or all selfies for the
    current uid (when no key). Server enforces `selfies/{uid}/` prefix on every
    delete — cross-user attempts get 403."""
    uid = user["uid"]
    expected_prefix = _selfies_prefix(uid)

    if key is not None:
        if not key.startswith(expected_prefix):
            raise HTTPException(status_code=403, detail="key does not belong to current user")
        try:
            _r2.delete_object(key, bucket=settings.r2_selfies_bucket)
        except _r2.R2NotConfigured as exc:
            raise HTTPException(status_code=500, detail=f"r2_not_configured: {exc}")
        return {"deleted": key}

    try:
        deleted = _r2.delete_prefix(expected_prefix, bucket=settings.r2_selfies_bucket)
    except _r2.R2NotConfigured as exc:
        raise HTTPException(status_code=500, detail=f"r2_not_configured: {exc}")
    return {"deleted_count": deleted, "prefix": expected_prefix}


_mount_static(app)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    uvicorn.run("src.speech_to_video.api.server:app", host=host, port=port, reload=os.getenv("RELOAD", "0") in {"1", "true", "on", "yes"})
