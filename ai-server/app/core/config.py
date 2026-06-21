import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    ai_detection_provider: str = os.getenv("AI_DETECTION_PROVIDER", "mock")
    ai_commerce_query_provider: str = os.getenv(
        "AI_COMMERCE_QUERY_PROVIDER",
        os.getenv("AI_DETECTION_PROVIDER", "mock"),
    )
    gms_openai_api_key: str | None = os.getenv("GMS_OPENAI_API_KEY")
    gms_openai_chat_completions_url: str = os.getenv(
        "GMS_OPENAI_CHAT_COMPLETIONS_URL",
        "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions",
    )
    gms_openai_model: str = os.getenv("GMS_OPENAI_MODEL", "gpt-5.4-mini")
    gms_openai_query_model: str = os.getenv(
        "GMS_OPENAI_QUERY_MODEL",
        os.getenv("GMS_OPENAI_MODEL", "gpt-5.4-mini"),
    )
    gms_openai_timeout_sec: float = float(os.getenv("GMS_OPENAI_TIMEOUT_SEC", "30"))


settings = Settings()
