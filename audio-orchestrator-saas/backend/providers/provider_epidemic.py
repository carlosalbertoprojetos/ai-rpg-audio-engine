"""Epidemic Sound provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider


class EpidemicProvider(BaseAudioProvider):
    """Retrieves royalty-free assets from Epidemic Sound."""

    provider_name = "epidemic"
    default_license = "royalty_free"
