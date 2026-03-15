"""Main orchestration pipeline for semantic-to-audio generation."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from backend.models.audio_asset import AudioAsset, AudioGenerationResponse, GenerationLayerResult
from backend.models.audio_request import AudioRequest
from backend.orchestration.provider_selector import ProviderSelector
from backend.providers.base import BaseAudioProvider, ProviderContext
from backend.providers.provider_aiva import AivaProvider
from backend.providers.provider_artlist import ArtlistProvider
from backend.providers.provider_epidemic import EpidemicProvider
from backend.providers.provider_freesound import FreesoundProvider
from backend.providers.provider_mubert import MubertProvider
from backend.providers.provider_shutterstock import ShutterstockProvider
from backend.services.audio_layer_engine import AudioLayerEngine
from backend.services.audio_mixer import AudioMixer
from backend.services.licensing_validator import LicensingValidator
from backend.services.semantic_audio_parser import SemanticAudioParser
from backend.storage.cache import SceneCache
from backend.storage.database import Database


class AudioPipeline:
    """Coordinates semantic parsing, provider retrieval, and final mixing."""

    def __init__(self, output_dir: Path, cache: SceneCache, database: Database) -> None:
        self.output_dir = output_dir
        self.cache = cache
        self.database = database

        self.parser = SemanticAudioParser()
        self.layer_engine = AudioLayerEngine()
        self.selector = ProviderSelector()
        self.validator = LicensingValidator()
        self.mixer = AudioMixer()

        provider = ShutterstockProvider()
        self.providers: dict[str, BaseAudioProvider] = {
            "freesound": FreesoundProvider(),
            "artlist": ArtlistProvider(),
            "epidemic": EpidemicProvider(),
            "shutterstock": provider,
            "adobe_stock": provider,
            "aiva": AivaProvider(),
            "mubert": MubertProvider(),
        }

    def generate(self, request: AudioRequest) -> AudioGenerationResponse:
        payload = request.model_dump()
        cache_key = self.cache.build_key(payload)
        cached = self.cache.get(cache_key)
        if cached is not None:
            cached_payload = {**cached, "cached": True}
            return AudioGenerationResponse(**cached_payload)

        scene_id = uuid4().hex
        request_id = uuid4().hex
        profile = self.parser.parse(request.prompt)
        layers = self.layer_engine.build_layers(profile, request.max_layers)

        assets: list[AudioAsset] = []
        layer_results: list[GenerationLayerResult] = []
        context = ProviderContext(prompt=request.prompt, profile=profile)

        for layer in layers:
            selected_asset = self._resolve_asset(scene_id, layer, context)
            assets.append(selected_asset)
            layer_results.append(
                GenerationLayerResult(
                    layer_id=layer.layer_id,
                    label=layer.label,
                    provider=selected_asset.provider,
                    asset_id=selected_asset.asset_id,
                    license_type=selected_asset.license_type,
                    volume=layer.volume,
                )
            )

        output_format = request.output_format
        output_basename = f"scene-{scene_id}"
        output_path = self.mixer.mix(layers=layers, output_path=self.output_dir / output_basename, output_format=output_format)
        actual_format = output_path.suffix.lstrip(".")
        audio_url = f"/api/audio/{output_path.name}"

        response = AudioGenerationResponse(
            scene_id=scene_id,
            audio_url=audio_url,
            output_format=actual_format,
            cached=False,
            layers=layer_results,
        )

        self.database.insert_request(request_id=request_id, prompt=request.prompt, output_format=actual_format)
        self.database.insert_scene(
            scene_id=scene_id,
            request_id=request_id,
            output_path=str(output_path),
            output_format=actual_format,
            cached=False,
        )
        self.database.insert_assets(scene_id=scene_id, assets=assets)

        cache_payload = response.model_dump()
        self.cache.set(cache_key, cache_payload)
        return response

    def _resolve_asset(self, scene_id: str, layer, context: ProviderContext) -> AudioAsset:
        providers = self.selector.select(layer)
        for provider_name in providers:
            provider = self.providers.get(provider_name)
            if provider is None:
                continue
            try:
                asset = provider.fetch_asset(layer, context)
                if not self.validator.validate(asset.license_type):
                    self.database.insert_provider_log(
                        scene_id=scene_id,
                        layer_id=layer.layer_id,
                        provider=provider_name,
                        status="rejected",
                        detail=f"License not compatible: {asset.license_type}",
                    )
                    continue
                self.database.insert_provider_log(
                    scene_id=scene_id,
                    layer_id=layer.layer_id,
                    provider=provider_name,
                    status="selected",
                    detail=asset.asset_id,
                )
                return asset
            except Exception as exc:
                self.database.insert_provider_log(
                    scene_id=scene_id,
                    layer_id=layer.layer_id,
                    provider=provider_name,
                    status="error",
                    detail=str(exc),
                )
        raise RuntimeError(f"No valid provider found for layer {layer.layer_id}")
