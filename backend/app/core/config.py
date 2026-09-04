"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root so settings load whether CWD is backend/ or the repo root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Settings required to run the REVIVE API.

    Values are read from environment variables and optionally from a .env file
    located in the repository root or the backend directory.
    """

    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "REVIVE API"
    database_url: str
    redis_url: str
    cors_origins: str = "http://localhost:3000"
    razorpay_webhook_secret: str

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated origins from the environment."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached, validated environment configuration."""
    return Settings()
