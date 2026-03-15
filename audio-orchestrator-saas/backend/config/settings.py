"""Runtime settings for the audio orchestrator SaaS."""
from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Audio Orchestrator SaaS"
    api_prefix: str = "/api"
    output_dir: Path = Path("generated_audio")
    database_path: Path = Path("audio_orchestrator.db")
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 1800
    default_export_format: str = "wav"

    freesound_api_key: str | None = Field(default=None, alias="FREESOUND_API_KEY")
    epidemic_api_key: str | None = Field(default=None, alias="EPIDEMIC_API_KEY")
    artlist_api_key: str | None = Field(default=None, alias="ARTLIST_API_KEY")
    shutterstock_api_key: str | None = Field(default=None, alias="SHUTTERSTOCK_API_KEY")
    adobe_stock_api_key: str | None = Field(default=None, alias="ADOBE_STOCK_API_KEY")
    aiva_api_key: str | None = Field(default=None, alias="AIVA_API_KEY")
    mubert_api_key: str | None = Field(default=None, alias="MUBERT_API_KEY")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.database_path.parent.mkdir(parents=True, exist_ok=True)
