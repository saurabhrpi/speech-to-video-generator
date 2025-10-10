import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    # Force .env to override any existing environment variables for dev convenience
    load_dotenv(override=True)
except Exception:
    # dotenv is optional at runtime
    pass


@dataclass
class Settings:
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_org_id: str = os.environ.get("OPENAI_ORG_ID", "")
    openai_project: str = os.environ.get("OPENAI_PROJECT", "")
    aimlapi_api_key: str = os.environ.get("AIMLAPI_API_KEY", "")
    aimlapi_base_url: str = os.environ.get("AIMLAPI_BASE_URL", "https://api.aimlapi.com/v2")
    aimlapi_generate_path: str = os.environ.get("AIMLAPI_GENERATE_PATH", "/generate/video/alibaba/generation")
    aimlapi_status_path: str = os.environ.get("AIMLAPI_STATUS_PATH", "/generate/video/alibaba/generation")
    aimlapi_status_query_param: str = os.environ.get("AIMLAPI_STATUS_QUERY_PARAM", "generation_id")
    openai_chat_model: str = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4")
    openai_transcribe_model: str = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    default_fps: int = int(os.environ.get("DEFAULT_FPS", "30"))
    default_resolution_high: str = os.environ.get("DEFAULT_RES_HIGH", "1080p")
    default_resolution_medium: str = os.environ.get("DEFAULT_RES_MEDIUM", "720p")
    default_clip_seconds: int = int(os.environ.get("DEFAULT_CLIP_SECONDS", "10"))
    debug_transcript: bool = os.environ.get("DEBUG_TRANSCRIPT", "0").lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    return Settings()


