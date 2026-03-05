"""System orchestrator that wires all modules together."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

from config.system_config import SystemConfig, load_system_config
from core_math.emotional_field import EmotionalManifold
from psychoacoustic_encoder.feature_extractor import PsychoacousticFeatureExtractor
from psychoacoustic_encoder.model import ResidualCNNEncoder
from emotional_geometry.mapper import EmotionalMapper
from temporal_dynamics.transformer_model import TemporalTransformer
from generative_models.diffusion_model import ConditionedDiffusionModel
from generative_models.vae_model import TopologicalVAE
from multiobjective_engine.loss_engine import LossEngine
from collective_dynamics.collective_field import CollectiveField
from legal_risk.similarity_engine import SimilarityEngine


@dataclass
class SystemOrchestrator:
    """Coordinates module lifecycle and cross-module consistency checks."""

    config_path: Path

    def __post_init__(self) -> None:
        self.config: SystemConfig = load_system_config(self.config_path)
        self.modules: Dict[str, Any] = {}

    def instantiate_modules(self) -> Dict[str, Any]:
        """Instantiate all modules using shared typed configuration."""

        manifold = EmotionalManifold(dimension=self.config.emotional_dimension)
        extractor = PsychoacousticFeatureExtractor()
        encoder = ResidualCNNEncoder(embedding_dim=self.config.embedding_dimension)
        mapper = EmotionalMapper(
            input_dim=self.config.embedding_dimension,
            emotional_dim=self.config.emotional_dimension,
        )
        transformer = TemporalTransformer(
            input_dim=self.config.emotional_dimension,
            model_dim=64,
            num_layers=6,
            num_heads=8,
        )
        diffusion = ConditionedDiffusionModel(
            latent_dim=self.config.embedding_dimension,
            condition_dim=self.config.emotional_dimension,
        )
        vae = TopologicalVAE(
            input_dim=self.config.embedding_dimension,
            latent_dim=32,
        )
        loss_engine = LossEngine.from_config(self.config.loss_weights)
        collective = CollectiveField(kappa=self.config.kappa_collective)
        legal = SimilarityEngine(threshold=0.88)

        self.modules = {
            "manifold": manifold,
            "extractor": extractor,
            "encoder": encoder,
            "mapper": mapper,
            "transformer": transformer,
            "diffusion": diffusion,
            "vae": vae,
            "loss_engine": loss_engine,
            "collective": collective,
            "legal": legal,
        }
        return self.modules

    def validate_dependencies(self) -> bool:
        """Validate interface-level dependencies and expected dimensional contracts."""

        if not self.modules:
            self.instantiate_modules()

        encoder: ResidualCNNEncoder = self.modules["encoder"]
        mapper: EmotionalMapper = self.modules["mapper"]
        diffusion: ConditionedDiffusionModel = self.modules["diffusion"]
        transformer: TemporalTransformer = self.modules["transformer"]

        checks = [
            encoder.embedding_dim == mapper.input_dim,
            mapper.emotional_dim == transformer.input_dim,
            diffusion.latent_dim == encoder.embedding_dim,
            diffusion.condition_dim == mapper.emotional_dim,
        ]
        return all(checks)

    def ensure_mathematical_consistency(self) -> bool:
        """Ensure model-level stability assumptions are met before runtime."""

        if not self.modules:
            self.instantiate_modules()

        manifold: EmotionalManifold = self.modules["manifold"]
        stable, margin = manifold.check_stability(
            lambda_stability=self.config.lambda_stability,
            kappa_collective=self.config.kappa_collective,
        )
        return stable and margin > 0.0

    def bootstrap(self) -> Dict[str, Any]:
        """Full bootstrap sequence with dependency and consistency guarantees."""

        modules = self.instantiate_modules()
        if not self.validate_dependencies():
            raise RuntimeError("Dependency validation failed")
        if not self.ensure_mathematical_consistency():
            raise RuntimeError("Mathematical consistency validation failed")
        return modules


def build_orchestrator(config_path: str | Path = "config/system_config.yaml") -> SystemOrchestrator:
    """Factory helper to create a preconfigured orchestrator."""

    return SystemOrchestrator(config_path=Path(config_path))
