"""Benchmark runner for quantitative and simulated evaluation."""
from __future__ import annotations

from typing import Dict, List

from orchestrator.system_orchestrator import build_orchestrator
from core_math.emotional_field import l2_norm


class BenchmarkRunner:
    """Runs simulated benchmarks over core modules."""

    def __init__(self) -> None:
        orchestrator = build_orchestrator()
        self.modules = orchestrator.bootstrap()
        self.config = orchestrator.config

    def run(self, n_trials: int = 10) -> Dict[str, float]:
        manifold = self.modules["manifold"]
        collective = self.modules["collective"]
        legal = self.modules["legal"]

        stable_count = 0
        penalties: List[float] = []

        for trial in range(n_trials):
            state = [0.6 - 0.1 * i + trial * 0.01 for i in range(self.config.emotional_dimension)]
            audio = [0.0] * self.config.emotional_dimension
            social = [0.0] * self.config.emotional_dimension

            trajectory = manifold.simulate(
                initial_state=state,
                audio_drive=audio,
                collective_drive=social,
                lambda_stability=self.config.lambda_stability,
                kappa_collective=self.config.kappa_collective,
                dt=0.1,
                steps=40,
            )
            if l2_norm(trajectory[-1]) < l2_norm(trajectory[0]):
                stable_count += 1

            collective_center = collective.weighted_mean([trajectory[-1], [0.0] * self.config.emotional_dimension])
            risk = legal.evaluate_risk(trajectory[-1], collective_center)
            penalties.append(float(risk["penalty"]))

        return {
            "stability_rate": stable_count / max(n_trials, 1),
            "avg_legal_penalty": sum(penalties) / max(len(penalties), 1),
        }

    def report(self, n_trials: int = 10) -> str:
        metrics = self.run(n_trials=n_trials)
        return (
            "Benchmark Report\n"
            f"- Stability rate: {metrics['stability_rate']:.3f}\n"
            f"- Average legal penalty: {metrics['avg_legal_penalty']:.6f}\n"
        )
