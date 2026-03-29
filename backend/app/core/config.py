"""Uygulama ayarları — .env dosyasından pydantic-settings ile yüklenir."""

from __future__ import annotations

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Groq, MongoDB, CORS ve generation parametreleri."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "llama3-8b-8192"

    # Generation
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 2048
    TOP_P: float = 0.9

    # Retry / Timeout
    MAX_RETRIES: int = 2
    REQUEST_TIMEOUT: int = 30
    STREAM_TIMEOUT: int = 60
    HEALTH_TIMEOUT: int = 5

    # MongoDB
    MONGO_URL: str = "mongodb://localhost:27017/testflow"
    MONGO_DB: str = "testflow"

    # CORS — .env'de virgülle ayrılmış string olarak tutulur
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
