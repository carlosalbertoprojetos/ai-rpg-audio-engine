"""Semantic parser for free-form audio scene prompts."""
from __future__ import annotations

from dataclasses import dataclass

from backend.models.audio_request import SemanticProfile


@dataclass(frozen=True)
class KeywordMap:
    """Keyword dictionary used to classify prompt semantics."""

    emotion: dict[str, str]
    environment: dict[str, str]
    distance: dict[str, str]
    era: dict[str, str]
    sound_type: dict[str, str]


KEYWORDS = KeywordMap(
    emotion={
        "battle": "intense",
        "epic": "heroic",
        "whisper": "tense",
        "dark": "tense",
        "calm": "calm",
        "mystic": "mysterious",
    },
    environment={
        "forest": "outdoor",
        "cave": "indoor",
        "corridor": "indoor",
        "city": "urban",
        "battlefield": "outdoor",
        "sea": "outdoor",
    },
    distance={
        "distant": "far",
        "far": "far",
        "close": "near",
        "near": "near",
        "surrounding": "mid",
    },
    era={
        "medieval": "medieval",
        "futuristic": "future",
        "cyberpunk": "future",
        "roman": "ancient",
        "victorian": "industrial",
    },
    sound_type={
        "ambience": "environment",
        "ambient": "environment",
        "wind": "environment",
        "music": "cinematic_music",
        "cinematic": "cinematic_music",
        "dynamic": "dynamic_music",
        "battle": "environment",
        "voice": "human_voice",
        "whisper": "human_voice",
        "commercial": "commercial_asset",
    },
)


class SemanticAudioParser:
    """Parses user prompt into structured semantic profile."""

    def parse(self, prompt: str) -> SemanticProfile:
        normalized = prompt.lower().strip()
        tokens = [token.strip(" ,.!?;:") for token in normalized.split()]

        emotion = self._pick_value(tokens, KEYWORDS.emotion, default="neutral")
        environment = self._pick_value(tokens, KEYWORDS.environment, default="generic")
        distance = self._pick_value(tokens, KEYWORDS.distance, default="mid")
        era = self._pick_value(tokens, KEYWORDS.era, default="timeless")
        sound_type = self._pick_value(tokens, KEYWORDS.sound_type, default="environment")
        intensity = self._estimate_intensity(tokens)

        return SemanticProfile(
            emotion=emotion,
            intensity=intensity,
            environment=environment,
            distance=distance,
            era=era,
            sound_type=sound_type,
        )

    def _pick_value(self, tokens: list[str], mapping: dict[str, str], default: str) -> str:
        for token in tokens:
            if token in mapping:
                return mapping[token]
            for key, value in mapping.items():
                if token.startswith(key):
                    return value
        return default

    def _estimate_intensity(self, tokens: list[str]) -> float:
        score = 0.45
        high_intensity_markers = {"epic", "battle", "intense", "explosion", "war"}
        low_intensity_markers = {"calm", "soft", "whisper", "distant"}

        for token in tokens:
            if token in high_intensity_markers:
                score += 0.15
            if token in low_intensity_markers:
                score -= 0.08

        return max(0.1, min(1.0, score))
