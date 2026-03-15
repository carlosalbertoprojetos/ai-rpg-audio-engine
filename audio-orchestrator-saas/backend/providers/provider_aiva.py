"""AIVA provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider


class AivaProvider(BaseAudioProvider):
    """Generates cinematic music through AIVA-compatible workflow."""

    provider_name = "aiva"
    default_license = "commercial_safe"
