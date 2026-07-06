from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Required
    GEMINI_API_KEY: str
    GEOAPIFY_API_KEY: str

    # Optional
    GROQ_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    QDRANT_URL: Optional[str] = None
    QDRANT_PORT: Optional[int] = None

    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None

    LANGSMITH_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()