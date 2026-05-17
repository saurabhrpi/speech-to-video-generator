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
    openai_chat_model: str = os.environ.get("OPENAI_CHAT_MODEL", "gpt-5.2")
    openai_transcribe_model: str = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    default_fps: int = int(os.environ.get("DEFAULT_FPS", "30"))
    default_resolution_high: str = os.environ.get("DEFAULT_RES_HIGH", "1080p")
    default_resolution_medium: str = os.environ.get("DEFAULT_RES_MEDIUM", "720p")
    default_clip_seconds: int = int(os.environ.get("DEFAULT_CLIP_SECONDS", "10"))
    debug_transcript: bool = os.environ.get("DEBUG_TRANSCRIPT", "0").lower() in {"1", "true", "yes", "on"}
    kling_i2v_model: str = os.environ.get("KLING_I2V_MODEL", "klingai/video-v3-pro-image-to-video")
    kling_t2v_model: str = os.environ.get("KLING_T2V_MODEL", "klingai/video-v3-standard-text-to-video")
    seedance_i2v_model: str = os.environ.get("SEEDANCE_I2V_MODEL", "bytedance/seedance-1-0-pro-i2v")
    hailuo_t2v_model: str = os.environ.get("HAILUO_T2V_MODEL", "minimax/hailuo-02")
    hailuo_23_t2v_model: str = os.environ.get("HAILUO_23_T2V_MODEL", "minimax/hailuo-2.3")
    hailuo_23_fast_i2v_model: str = os.environ.get("HAILUO_23_FAST_I2V_MODEL", "minimax/hailuo-2.3-fast")
    hailuo_i2v_model: str = os.environ.get("HAILUO_I2V_MODEL", "minimax/hailuo-02")
    i2v_model: str = os.environ.get("I2V_MODEL", "minimax/hailuo-02")
    i2v_resolution: str = os.environ.get("I2V_RESOLUTION", "768P")
    i2v_duration: int = int(os.environ.get("I2V_DURATION", "6"))
    nano_banana_t2i_model: str = os.environ.get("NANO_BANANA_T2I_MODEL", "google/nano-banana-pro")
    nano_banana_edit_model: str = os.environ.get("NANO_BANANA_EDIT_MODEL", "google/nano-banana-pro-edit")
    minimax_api_key: str = os.environ.get("MINIMAX_API_KEY", "")
    kling_access_key: str = os.environ.get("KLING_ACCESS_KEY", "")
    kling_secret_key: str = os.environ.get("KLING_SECRET_KEY", "")
    kling_api_base_url: str = os.environ.get("KLING_API_BASE_URL", "https://api-singapore.klingai.com")
    firebase_service_account_path: str = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    firebase_service_account_json: str = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    revenuecat_rest_api_key: str = os.environ.get("REVENUECAT_REST_API_KEY", "")
    r2_account_id: str = os.environ.get("R2_ACCOUNT_ID", "")
    r2_access_key_id: str = os.environ.get("R2_ACCESS_KEY_ID", "")
    r2_secret_access_key: str = os.environ.get("R2_SECRET_ACCESS_KEY", "")
    r2_bucket: str = os.environ.get("R2_BUCKET", "speech-to-video-templates")
    r2_selfies_bucket: str = os.environ.get("R2_SELFIES_BUCKET", "speech-to-video-selfies")
    r2_public_base_url: str = os.environ.get("R2_PUBLIC_BASE_URL", "https://assets.speech-2-video.ai")
    google_cloud_project: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    vertex_location: str = os.environ.get("VERTEX_LOCATION", "us-central1")
    vertex_service_account_json: str = os.environ.get("VERTEX_SERVICE_ACCOUNT_JSON", "")
    vertex_service_account_path: str = os.environ.get("VERTEX_SERVICE_ACCOUNT_PATH", "")
    vertex_nb_model: str = os.environ.get("VERTEX_NB_MODEL", "gemini-2.5-flash-image")
    # Google AI Studio direct (paid tier) — Pipeline A NBP regen step + future
    # Pipeline B Edit migration (AIV-91). Case-tolerant: `.env` ships
    # `NBP_API_Key` (camelCase) but accept `NBP_API_KEY` too.
    nbp_api_key: str = os.environ.get("NBP_API_Key") or os.environ.get("NBP_API_KEY", "")
    nbp_model: str = os.environ.get("NBP_MODEL", "gemini-3-pro-image-preview")


def get_settings() -> Settings:
    return Settings()


