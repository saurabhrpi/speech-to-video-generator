import os
import tempfile
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
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

# Session middleware for login state (already used by OAuth)
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
COOKIE_SAMESITE = (os.getenv("SESSION_COOKIE_SAMESITE", "lax").lower() or "lax")
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    COOKIE_SAMESITE = "lax"
COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0").lower() in {"1", "true", "yes", "on"}
COOKIE_MAX_AGE = int(os.getenv("SESSION_COOKIE_MAX_AGE", str(60 * 60 * 24 * 30)))  # 30 days default
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site=COOKIE_SAMESITE,
    https_only=COOKIE_SECURE,
    max_age=COOKIE_MAX_AGE,
)

oauth = OAuth()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
POST_LOGIN_REDIRECT = os.getenv("POST_LOGIN_REDIRECT", "").rstrip("/")
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# Session middleware for login state
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="lax")

# OAuth (Google)
oauth = OAuth()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
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


# --------- Auth and usage limiting ---------
_UNAUTH_LIMIT = int(os.getenv("UNAUTH_GEN_LIMIT", "5"))
_IP_USAGE: dict[str, int] = {}

def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    try:
        return request.client.host or "unknown"
    except Exception:
        return "unknown"

def _usage_key(request: Request) -> str:
    ua = request.headers.get("user-agent", "?")
    return f"{_client_ip(request)}|{ua[:120]}"

def _get_usage(request: Request) -> int:
    # If authenticated, rely solely on session (persists across visits for max_age)
    # If unauthenticated, use the higher of session vs ephemeral IP+UA bucket.
    sess = int(request.session.get("usage_count", 0))
    if request.session.get("user"):
        return sess
    ipk = _usage_key(request)
    ipu = int(_IP_USAGE.get(ipk, 0))
    return max(sess, ipu)

def _inc_usage(request: Request) -> int:
    newv = _get_usage(request) + 1
    request.session["usage_count"] = newv
    if not request.session.get("user"):
        _IP_USAGE[_usage_key(request)] = newv
    return newv

@app.get("/api/auth/session")
def auth_session(request: Request):
    user = request.session.get("user")
    return {"authenticated": bool(user), "user": user or None, "usage_count": _get_usage(request), "limit": _UNAUTH_LIMIT}

@app.get("/api/auth/login")
async def auth_login(request: Request):
    client = oauth.create_client("google")
    if client is None:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    # Optional 'next' for post-login redirect
    next_url = request.query_params.get("next")
    if next_url:
        request.session["plr"] = next_url
    redirect_uri = request.url_for("auth_callback")
    # On Replit/public deploys, force an absolute URL that matches Google console
    if PUBLIC_BASE_URL:
        redirect_uri = f"{PUBLIC_BASE_URL}/api/auth/callback"
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/callback")
async def auth_callback(request: Request):
    client = oauth.create_client("google")
    if client is None:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"oauth_exchange_failed: {exc}")
    userinfo = token.get("userinfo") or {}
    if not userinfo:
        try:
            userinfo = await client.parse_id_token(request, token)
        except Exception as exc:
            userinfo = {}
    if not userinfo:
        raise HTTPException(status_code=401, detail="Failed to retrieve user info")
    request.session["user"] = {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }
    # Redirect back to app
    dest = request.session.pop("plr", None) or POST_LOGIN_REDIRECT or PUBLIC_BASE_URL or "/"
    return HTMLResponse(f"<script>window.location='{dest}'</script>")

@app.post("/api/auth/logout")
def auth_logout(request: Request):
    request.session.clear()
    return {"success": True}


@app.post("/api/generate")
def generate_video(request: Request, prompt: str = Form(...), duration: int = Form(10), quality: str = Form("high")):
    # Enforce unauthenticated usage limit
    if not request.session.get("user") and _get_usage(request) >= _UNAUTH_LIMIT:
        raise HTTPException(status_code=401, detail="login_required")
    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(status_code=400, detail="Prompt is required")
    result = service.generate_video(prompt=prompt.strip(), duration=int(duration), quality=quality)
    if result.get("success") or result.get("video_url"):
        _inc_usage(request)
    return JSONResponse(result)


@app.post("/api/speech-to-video")
async def speech_to_video(
    request: Request,
    audio: UploadFile = File(...),
    duration: int = Form(10),
    quality: str = Form("high"),
    prompt: Optional[str] = Form(None),
):
    # Enforce unauthenticated usage limit
    if not request.session.get("user") and _get_usage(request) >= _UNAUTH_LIMIT:
        raise HTTPException(status_code=401, detail="login_required")
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
        if result.get("success") or result.get("video_url"):
            _inc_usage(request)
        return JSONResponse(result)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@app.get("/api/clips")
def get_clips(request: Request):
    # Scope clips by environment namespace and user (if authenticated)
    ns = os.getenv("CLIPS_NAMESPACE", "")
    user = request.session.get("user") or {}
    user_ns = user.get("sub") or ""
    namespace = "/".join([p for p in [ns, user_ns] if p]) or None
    return JSONResponse(list_clips(namespace))


@app.post("/api/clips")
def save_clip(request: Request, url: str = Form(...), note: Optional[str] = Form(None)):
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    ns = os.getenv("CLIPS_NAMESPACE", "")
    user = request.session.get("user") or {}
    user_ns = user.get("sub") or ""
    namespace = "/".join([p for p in [ns, user_ns] if p]) or None
    entry = add_clip(url, note, namespace)
    return JSONResponse({"success": True, "saved": entry})


@app.delete("/api/clips")
def delete_clips(request: Request):
    ns = os.getenv("CLIPS_NAMESPACE", "")
    user = request.session.get("user") or {}
    user_ns = user.get("sub") or ""
    namespace = "/".join([p for p in [ns, user_ns] if p]) or None
    clear_clips(namespace)
    return JSONResponse({"success": True, "cleared": True})


@app.post("/api/stitch")
def stitch(urls: Optional[str] = Form(None), use_saved: bool = Form(False)):
    url_list: List[str] = []
    if use_saved:
        items = list_clips()
        filtered: List[str] = []
        for i in items:
            u = (i.get("url") or "").strip()
            note = (i.get("note") or "").strip().lower()
            if not u:
                continue
            # Ignore previously stitched entries and non-absolute URLs
            if u.startswith("/api/stitched") or u.endswith("/api/stitched"):
                continue
            if "stitched" in note:
                continue
            if not (u.startswith("http://") or u.startswith("https://")):
                continue
            filtered.append(u)
        # de-duplicate while preserving order
        seen = set()
        url_list = [x for x in filtered if not (x in seen or seen.add(x))]
    else:
        if urls:
            # Accept comma or newline separated
            parts = [p.strip() for p in urls.replace("\n", ",").split(",")]
            # keep only absolute http(s) urls
            url_list = [p for p in parts if p and (p.startswith("http://") or p.startswith("https://"))]
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


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribe an uploaded audio file and return the text.
    """
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


