"""Models for audio assets and response payloads."""
from __future__ import annotations

from pydantic import BaseModel


class AudioAsset(BaseModel):
    """Audio asset returned by one provider."""

    asset_id: str
    provider: str
    title: str
    source_url: str
    local_path: str | None = None
    license_type: str
    duration_seconds: float
    layer_id: str


class GenerationLayerResult(BaseModel):
    """Summary of one generated layer and chosen provider asset."""

    layer_id: str
    label: str
    provider: str
    asset_id: str
    license_type: str
    volume: float


class AudioGenerationResponse(BaseModel):
    """Public API response for audio generation."""

    scene_id: str
    audio_url: str
    output_format: str
    cached: bool
    layers: list[GenerationLayerResult]
