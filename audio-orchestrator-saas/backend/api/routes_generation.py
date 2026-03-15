"""Generation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_pipeline
from backend.models.audio_asset import AudioGenerationResponse
from backend.models.audio_request import AudioRequest
from backend.orchestration.audio_pipeline import AudioPipeline

router = APIRouter(tags=["generation"])


@router.post("/generate-audio", response_model=AudioGenerationResponse)
def generate_audio(
    request: AudioRequest,
    pipeline: AudioPipeline = Depends(get_pipeline),
) -> AudioGenerationResponse:
    try:
        return pipeline.generate(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"generation failed: {exc}") from exc
