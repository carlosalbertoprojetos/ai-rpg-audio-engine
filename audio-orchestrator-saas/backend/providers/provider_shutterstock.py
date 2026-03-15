"""Shutterstock and Adobe Stock provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider, ProviderContext
from backend.models.audio_asset import AudioAsset
from backend.models.audio_request import SceneLayer


class ShutterstockProvider(BaseAudioProvider):
    """Retrieves commercial-safe stock assets from Shutterstock/Adobe catalogs."""

    provider_name = "shutterstock"
    default_license = "standard_commercial"

    def fetch_asset(self, layer: SceneLayer, context: ProviderContext) -> AudioAsset:
        asset = super().fetch_asset(layer, context)
        # Adobe Stock is supported through the same commercial adapter path.
        if "adobe" in context.prompt.lower():
            return asset.model_copy(update={"provider": "adobe_stock"})
        return asset
