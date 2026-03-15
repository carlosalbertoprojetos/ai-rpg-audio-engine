"""Test bootstrap for audio orchestrator backend."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    from backend.api import deps
    from backend.config.settings import settings

    output_dir = tmp_path / "generated"
    db_path = tmp_path / "test.db"
    output_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(settings, "output_dir", output_dir)
    monkeypatch.setattr(settings, "database_path", db_path)
    monkeypatch.setattr(settings, "redis_url", "redis://localhost:6399/0")
    deps.get_pipeline.cache_clear()
    yield
    deps.get_pipeline.cache_clear()
