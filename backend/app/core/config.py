from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RPGSoundDesk"
    environment: str = "dev"
    api_prefix: str = "/api/v1"

    postgres_dsn: str = "postgresql+psycopg://rpg:rpg@postgres:5432/rpgsounddesk"
    redis_url: str = "redis://redis:6379/0"

    s3_endpoint_url: str = "http://minio:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "rpgsounddesk-audio"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    repository_mode: str = "in_memory"
    event_bus_mode: str = "in_memory"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 120
    sound_event_poll_interval_seconds: float = 2.0
    otel_enabled: bool = False
    otel_service_name: str = "rpgsounddesk-backend"
    otel_exporter_otlp_endpoint: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
