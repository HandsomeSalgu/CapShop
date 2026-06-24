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


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    try:
        return int(value.strip().strip('"').strip("'"))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    try:
        return float(value.strip().strip('"').strip("'"))
    except ValueError:
        return default


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
    gemini_api_key: str | None = _env_optional_str("GEMINI_API_KEY")
    gemini_model: str = _env_str("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_vision_model: str = _env_str(
        "GEMINI_VISION_MODEL",
        _env_str("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    gemini_query_model: str = _env_str(
        "GEMINI_QUERY_MODEL",
        _env_str("GEMINI_MODEL", "gemini-2.5-flash"),
    )
    gemini_generate_content_url_template: str = _env_str(
        "GEMINI_GENERATE_CONTENT_URL_TEMPLATE",
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    )
    gemini_timeout_sec: float = _env_float("GEMINI_TIMEOUT_SEC", 30.0)
    http_timeout_sec: float = _env_float("HTTP_TIMEOUT_SEC", gemini_timeout_sec)
    backend_base_url: str = _env_str("BACKEND_BASE_URL", "http://localhost:8080")
    backend_commerce_search_path: str = _env_str(
        "BACKEND_COMMERCE_SEARCH_PATH",
        "/api/commerce/search",
    )
    naver_shopping_provider: str = _env_str("NAVER_SHOPPING_PROVIDER", "backend")
    naver_shopping_display: int = int(os.getenv("NAVER_SHOPPING_DISPLAY", "30"))
    naver_shopping_sort: str = os.getenv("NAVER_SHOPPING_SORT", "sim")
    naver_search_max_workers: int = _env_int("AI_NAVER_SEARCH_MAX_WORKERS", 5)
    skip_gemini_min_candidates: int = _env_int("AI_SKIP_GEMINI_MIN_CANDIDATES", 20)
    skip_visual_rerank_top_score: float = _env_float("AI_SKIP_VISUAL_RERANK_TOP_SCORE", 0.75)
    skip_visual_rerank_avg_score: float = _env_float("AI_SKIP_VISUAL_RERANK_AVG_SCORE", 0.72)
    search_cache_ttl_seconds: int = _env_int("AI_SEARCH_CACHE_TTL_SECONDS", 3600)
    search_cache_max_size: int = _env_int("AI_SEARCH_CACHE_MAX_SIZE", 500)
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
    gemini_search_model: str = _env_str("GEMINI_SEARCH_MODEL", "gemini-2.5-flash")
    gemini_search_endpoint: str = _env_str(
        "GEMINI_SEARCH_ENDPOINT",
        "https://generativelanguage.googleapis.com/v1beta/interactions",
    )
    gemini_search_timeout_seconds: float = _env_float("GEMINI_SEARCH_TIMEOUT_SECONDS", 20.0)
    analysis_max_retries: int = int(os.getenv("AI_ANALYSIS_MAX_RETRIES", "0"))
    db_host: str = _env_str("DB_HOST", "localhost")
    db_port: int = int(_env_str("DB_PORT", "3306"))
    db_user: str = _env_str("DB_USER", "root")
    db_password: str = _env_str("DB_PASSWORD", "potato")
    db_name: str = _env_str("DB_NAME", "syncshopper")

settings = Settings()
