"""Provider interface and shared helper logic."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from backend.models.audio_asset import AudioAsset
from backend.models.audio_request import SceneLayer, SemanticProfile


@dataclass(frozen=True)
class ProviderContext:
    """Context passed to providers during retrieval/generation."""

    prompt: str
    profile: SemanticProfile


class BaseAudioProvider:
    """Base class for pluggable asset providers."""

    provider_name: str = "base"
    default_license: str = "royalty_free"

    def fetch_asset(self, layer: SceneLayer, context: ProviderContext) -> AudioAsset:
        """Return one best candidate asset for the requested scene layer."""

        asset_id = f"{self.provider_name}-{uuid4().hex[:10]}"
        title = f"{layer.label} - {context.profile.environment}"
        source_url = self._build_source_url(layer, context)
        return AudioAsset(
            asset_id=asset_id,
            provider=self.provider_name,
            title=title,
            source_url=source_url,
            license_type=self.default_license,
            duration_seconds=layer.duration_seconds,
            layer_id=layer.layer_id,
        )

    def _build_source_url(self, layer: SceneLayer, context: ProviderContext) -> str:
        slug = context.prompt.lower().replace(" ", "-")[:60]
        return f"https://assets.example/{self.provider_name}/{layer.sound_type}/{slug}.wav"
