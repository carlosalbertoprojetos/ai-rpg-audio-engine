"""Caching layer with Redis backend and in-memory fallback."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass
class _MemoryItem:
    value: str
    expires_at: float


class SceneCache:
    """Stores generated scene metadata keyed by hashed request parameters."""

    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._memory: dict[str, _MemoryItem] = {}
        self._redis = None
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    def build_key(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        if self._redis is not None:
            value = self._redis.get(key)
            if value:
                return json.loads(value)
            return None

        item = self._memory.get(key)
        if item is None:
            return None
        if item.expires_at < time.time():
            self._memory.pop(key, None)
            return None
        return json.loads(item.value)

    def set(self, key: str, value: dict[str, Any]) -> None:
        serialized = json.dumps(value)
        if self._redis is not None:
            self._redis.setex(key, self._ttl_seconds, serialized)
            return
        self._memory[key] = _MemoryItem(
            value=serialized,
            expires_at=time.time() + self._ttl_seconds,
        )
