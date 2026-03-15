"""Build layered scene composition from semantic profile."""
from __future__ import annotations

from uuid import uuid4

from backend.models.audio_request import SceneLayer, SemanticProfile


class AudioLayerEngine:
    """Generates layered arrangements based on semantic profile."""

    def build_layers(self, profile: SemanticProfile, max_layers: int) -> list[SceneLayer]:
        layers: list[SceneLayer] = []

        if profile.sound_type in {"environment", "human_voice"}:
            layers.append(self._layer("base-ambience", "Ambient Bed", "environment", profile, 0.65, 24.0))
            layers.append(self._layer("detail-fx", "Scene Detail", "environment", profile, 0.45, 18.0))
        if profile.sound_type in {"cinematic_music", "dynamic_music"}:
            layers.append(self._layer("music-core", "Musical Core", profile.sound_type, profile, 0.6, 30.0))
        if profile.sound_type == "commercial_asset":
            layers.append(self._layer("commercial-track", "Commercial Asset", "commercial_asset", profile, 0.7, 20.0))
        if "intense" in profile.emotion or profile.intensity > 0.7:
            layers.append(self._layer("impact-layer", "Impact Accents", "dynamic_music", profile, 0.52, 12.0))

        if not layers:
            layers.append(self._layer("fallback", "Fallback Ambient", "environment", profile, 0.6, 20.0))

        return layers[:max_layers]

    def _layer(
        self,
        label_seed: str,
        label: str,
        sound_type: str,
        profile: SemanticProfile,
        volume: float,
        duration_seconds: float,
    ) -> SceneLayer:
        adjusted_volume = max(0.1, min(1.0, volume * (0.8 + profile.intensity * 0.3)))
        return SceneLayer(
            layer_id=f"{label_seed}-{uuid4().hex[:8]}",
            label=label,
            sound_type=sound_type,
            intensity=profile.intensity,
            volume=adjusted_volume,
            duration_seconds=duration_seconds,
            distance=profile.distance,
            environment=profile.environment,
        )
