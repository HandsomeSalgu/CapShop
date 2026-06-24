import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE_PATH)


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    return value.strip().strip('"').strip("'")


def _env_optional_str(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip().strip('"').strip("'")

    return None


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    return value.strip().strip('"').strip("'").lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    ai_detection_provider: str = _env_str("AI_DETECTION_PROVIDER", "mock")
    ai_commerce_query_provider: str = os.getenv(
        "AI_COMMERCE_QUERY_PROVIDER",
        _env_str("AI_DETECTION_PROVIDER", "mock"),
    )
    ai_analysis_provider: str = os.getenv(
        "AI_ANALYSIS_PROVIDER",
        os.getenv("AI_COMMERCE_QUERY_PROVIDER", os.getenv("AI_DETECTION_PROVIDER", "mock")),
    )
    ai_visual_reranker_provider: str = os.getenv(
        "AI_VISUAL_RERANKER_PROVIDER",
        os.getenv("AI_ANALYSIS_PROVIDER", os.getenv("AI_COMMERCE_QUERY_PROVIDER", "mock")),
    )
    ai_result_judge_provider: str = os.getenv(
        "AI_RESULT_JUDGE_PROVIDER",
        os.getenv("AI_ANALYSIS_PROVIDER", os.getenv("AI_COMMERCE_QUERY_PROVIDER", "mock")),
    )
    gms_openai_api_key: str | None = os.getenv("GMS_OPENAI_API_KEY")
    gms_openai_chat_completions_url: str = _env_str(
        "GMS_OPENAI_CHAT_COMPLETIONS_URL",
        "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions",
    )
    gms_openai_embeddings_url: str = _env_str(
        "GMS_OPENAI_EMBEDDINGS_URL",
        "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings",
    )
    gms_openai_model: str = _env_str("GMS_OPENAI_MODEL", "gpt-5.4-mini")
    gms_openai_vision_model: str = _env_str(
        "GMS_OPENAI_VISION_MODEL",
        _env_str("GMS_OPENAI_MODEL", "gpt-5.4-mini"),
    )
    gms_openai_query_model: str = _env_str(
        "GMS_OPENAI_QUERY_MODEL",
        _env_str("GMS_OPENAI_MODEL", "gpt-5.4-mini"),
    )
    gms_openai_embedding_model: str = _env_str(
        "GMS_OPENAI_EMBEDDING_MODEL",
        "text-embedding-3-small",
    )
    gms_openai_timeout_sec: float = float(os.getenv("GMS_OPENAI_TIMEOUT_SEC", "30"))
    backend_base_url: str = _env_str("BACKEND_BASE_URL", "http://localhost:8080")
    backend_commerce_search_path: str = _env_str(
        "BACKEND_COMMERCE_SEARCH_PATH",
        "/api/commerce/search",
    )
    naver_shopping_provider: str = _env_str("NAVER_SHOPPING_PROVIDER", "backend")
    naver_shopping_display: int = int(os.getenv("NAVER_SHOPPING_DISPLAY", "30"))
    naver_shopping_sort: str = os.getenv("NAVER_SHOPPING_SORT", "sim")
    google_custom_search_provider: str = _env_str("GOOGLE_CUSTOM_SEARCH_PROVIDER", "google")
    google_custom_search_api_key: str | None = _env_optional_str(
        "GOOGLE_CSE_API_KEY",
        "GOOGLE_CUSTOM_SEARCH_API_KEY",
    )
    google_custom_search_cx: str | None = _env_optional_str(
        "GOOGLE_CSE_CX",
        "GOOGLE_CUSTOM_SEARCH_CX",
    )
    google_custom_search_url: str = _env_str(
        "GOOGLE_CUSTOM_SEARCH_URL",
        "https://customsearch.googleapis.com/customsearch/v1",
    )
    google_custom_search_display: int = int(os.getenv("GOOGLE_CUSTOM_SEARCH_DISPLAY", "5"))
    google_custom_search_strict_errors: bool = _env_bool("GOOGLE_CUSTOM_SEARCH_STRICT_ERRORS", False)
    gemini_api_key: str | None = _env_optional_str("GEMINI_API_KEY")
    gemini_search_model: str = _env_str("GEMINI_SEARCH_MODEL", "gemini-3.5-flash")
    gemini_search_endpoint: str = _env_str(
        "GEMINI_SEARCH_ENDPOINT",
        "https://generativelanguage.googleapis.com/v1beta/interactions",
    )
    gemini_search_timeout_seconds: float = float(os.getenv("GEMINI_SEARCH_TIMEOUT_SECONDS", "20"))
    analysis_max_retries: int = int(os.getenv("AI_ANALYSIS_MAX_RETRIES", "1"))


settings = Settings()
