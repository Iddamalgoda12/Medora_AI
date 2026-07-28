from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # -------------------------
    # LLM Configuration
    # -------------------------

    # Choose: gemini or lmstudio or groq
    LLM_PROVIDER: str = "lmstudio"

    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str ="Gemini 2.5 Flash Lite"

    # LM Studio
    LMSTUDIO_BASE_URL: str = "http://127.0.0.1:1234"
    LMSTUDIO_API_KEY: str = "lm-studio"
    LMSTUDIO_MODEL: str = ""

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str =""

    # -------------------------
    # APIs
    # -------------------------

    GEOAPIFY_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None

    # -------------------------
    # Qdrant
    # -------------------------

    QDRANT_URL: Optional[str] = None
    QDRANT_PORT: Optional[int] = None

    # -------------------------
    # Redis
    # -------------------------

    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None

    # -------------------------
    # LangSmith
    # -------------------------

    LANGSMITH_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()