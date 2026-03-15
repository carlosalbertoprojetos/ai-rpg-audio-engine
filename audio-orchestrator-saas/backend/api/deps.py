"""Dependency wiring for FastAPI routes."""
from __future__ import annotations

from functools import lru_cache

from backend.config.settings import settings
from backend.orchestration.audio_pipeline import AudioPipeline
from backend.storage.cache import SceneCache
from backend.storage.database import Database


@lru_cache
def get_pipeline() -> AudioPipeline:
    cache = SceneCache(redis_url=settings.redis_url, ttl_seconds=settings.cache_ttl_seconds)
    database = Database(path=settings.database_path)
    return AudioPipeline(output_dir=settings.output_dir, cache=cache, database=database)
