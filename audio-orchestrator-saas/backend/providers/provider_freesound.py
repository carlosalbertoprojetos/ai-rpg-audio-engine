"""Freesound provider adapter."""
from __future__ import annotations

from backend.providers.base import BaseAudioProvider


class FreesoundProvider(BaseAudioProvider):
    """Retrieves ambience and environmental assets from Freesound."""

    provider_name = "freesound"
    default_license = "cc_by"
