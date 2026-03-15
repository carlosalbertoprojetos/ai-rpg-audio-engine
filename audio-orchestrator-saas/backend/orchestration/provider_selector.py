"""Provider selection policy with fallback ordering."""
from __future__ import annotations

from backend.models.audio_request import SceneLayer


class ProviderSelector:
    """Chooses best providers based on layer sound type with fallbacks."""

    def select(self, layer: SceneLayer) -> list[str]:
        mapping: dict[str, list[str]] = {
            "environment": ["freesound", "epidemic", "artlist"],
            "cinematic_music": ["aiva", "artlist", "epidemic"],
            "dynamic_music": ["mubert", "aiva", "artlist"],
            "commercial_asset": ["shutterstock", "adobe_stock", "artlist"],
            "human_voice": ["freesound", "epidemic"],
        }
        return mapping.get(layer.sound_type, ["freesound", "artlist"])
