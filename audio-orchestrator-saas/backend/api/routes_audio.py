"""Audio retrieval endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config.settings import settings

router = APIRouter(tags=["audio"])


@router.get("/audio/{file_name}")
def get_audio(file_name: str) -> FileResponse:
    target = (settings.output_dir / file_name).resolve()
    base = settings.output_dir.resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="invalid filename")
    if not target.exists():
        raise HTTPException(status_code=404, detail="audio file not found")

    suffix = Path(file_name).suffix.lower()
    media_type = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
    }.get(suffix, "application/octet-stream")
    return FileResponse(path=target, media_type=media_type, filename=target.name)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
