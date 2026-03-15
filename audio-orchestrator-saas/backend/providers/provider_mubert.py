"""Mubert provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider


class MubertProvider(BaseAudioProvider):
    """Generates dynamic adaptive music through Mubert."""

    provider_name = "mubert"
    default_license = "commercial_safe"
