"""SQLite persistence for requests, scenes, assets, and provider logs."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.models.audio_asset import AudioAsset


@dataclass
class Database:
    """Simple repository abstraction over SQLite for orchestration records."""

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS audio_requests (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    output_format TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audio_scenes (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    output_format TEXT NOT NULL,
                    cached INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audio_assets (
                    id TEXT PRIMARY KEY,
                    scene_id TEXT NOT NULL,
                    layer_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    duration_seconds REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS provider_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT NOT NULL,
                    layer_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def insert_request(self, request_id: str, prompt: str, output_format: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audio_requests (id, prompt, output_format, created_at) VALUES (?, ?, ?, ?)",
                (request_id, prompt, output_format, self._now()),
            )

    def insert_scene(self, scene_id: str, request_id: str, output_path: str, output_format: str, cached: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO audio_scenes (id, request_id, output_path, output_format, cached, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (scene_id, request_id, output_path, output_format, int(cached), self._now()),
            )

    def insert_assets(self, scene_id: str, assets: list[AudioAsset]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO audio_assets (id, scene_id, layer_id, provider, title, source_url, license_type, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        asset.asset_id,
                        scene_id,
                        asset.layer_id,
                        asset.provider,
                        asset.title,
                        asset.source_url,
                        asset.license_type,
                        asset.duration_seconds,
                    )
                    for asset in assets
                ],
            )

    def insert_provider_log(self, scene_id: str, layer_id: str, provider: str, status: str, detail: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO provider_logs (scene_id, layer_id, provider, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (scene_id, layer_id, provider, status, detail, self._now()),
            )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
