"""Run the full autonomous auditory emotional engineering pipeline."""
from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.system_orchestrator import build_orchestrator
from temporal_dynamics.trainer import TemporalTrainer
from validation.benchmark import BenchmarkRunner


def build_synthetic_signal(length: int = 1024) -> list[float]:
    return [
        0.6 * math.sin(2 * math.pi * 220 * t / 16000)
        + 0.3 * math.sin(2 * math.pi * 440 * t / 16000)
        for t in range(length)
    ]


def main() -> None:
    orchestrator = build_orchestrator()
    modules = orchestrator.bootstrap()
    config = orchestrator.config

    signal = build_synthetic_signal()

    extractor = modules["extractor"]
    encoder = modules["encoder"]
    mapper = modules["mapper"]
    transformer = modules["transformer"]
    diffusion = modules["diffusion"]
    vae = modules["vae"]
    loss_engine = modules["loss_engine"]
    manifold = modules["manifold"]

    features = extractor.extract(signal)
    embedding = encoder.forward(features)
    emotional_state = mapper.forward(embedding)

    sequence = [
        emotional_state,
        [v * 0.95 for v in emotional_state],
        [v * 0.90 for v in emotional_state],
        [v * 0.85 for v in emotional_state],
    ]

    trainer = TemporalTrainer(transformer)
    predicted = transformer.forward(sequence)
    temporal_loss = trainer.total_loss(predicted, sequence, manifold)

    generated = diffusion.sample(emotional_state)
    vae_loss = vae.train_step(generated)

    loss_terms = diffusion.loss_components(
        generated=generated,
        target=embedding,
        generated_emotion=emotional_state,
        target_emotion=emotional_state,
        generated_topology=0.1,
        target_topology=0.1,
    )

    total_loss = loss_engine.compute_total(
        l_emotion=loss_terms["emotional"],
        l_psychoacoustic=loss_terms["spectral"],
        l_coherence=temporal_loss,
        l_economic=0.05,
        l_legal=0.0,
        l_topology=loss_terms["topological"],
    )

    stable, margin = manifold.check_stability(config.lambda_stability, config.kappa_collective)

    benchmark = BenchmarkRunner()
    report = benchmark.report(n_trials=8)

    print("Pipeline Metrics")
    print(f"- Stable criterion: {stable} (margin={margin:.3f})")
    print(f"- Encoder embedding dim: {len(embedding)}")
    print(f"- Temporal loss: {temporal_loss:.6f}")
    print(f"- VAE loss: {vae_loss:.6f}")
    print(f"- Total multiobjective loss: {total_loss:.6f}")
    print(report)


if __name__ == "__main__":
    main()
