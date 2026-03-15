"""Artlist provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider


class ArtlistProvider(BaseAudioProvider):
    """Retrieves curated cinematic tracks from Artlist."""

    provider_name = "artlist"
    default_license = "royalty_free"
