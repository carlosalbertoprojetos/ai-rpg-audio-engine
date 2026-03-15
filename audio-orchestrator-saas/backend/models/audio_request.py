"""Data models for audio request payloads."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AudioRequest(BaseModel):
    """Incoming request for scene generation."""

    prompt: str = Field(min_length=3, max_length=500)
    output_format: str = Field(default="wav", pattern="^(wav|mp3|ogg)$")
    max_layers: int = Field(default=4, ge=1, le=8)


class SemanticProfile(BaseModel):
    """Extracted semantic dimensions from user prompt."""

    emotion: str
    intensity: float
    environment: str
    distance: str
    era: str
    sound_type: str


class SceneLayer(BaseModel):
    """One layer in a composed audio scene."""

    layer_id: str
    label: str
    sound_type: str
    intensity: float
    volume: float
    duration_seconds: float
    distance: str
    environment: str
