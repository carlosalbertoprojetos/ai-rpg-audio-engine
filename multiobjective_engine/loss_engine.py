"""Multiobjective loss composition engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class LossWeights:
    """Weight set for composed objective function."""

    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 1.0
    delta: float = 1.0
    epsilon: float = 1.0
    zeta: float = 1.0


class LossEngine:
    """Evaluates and updates a weighted multiobjective loss."""

    def __init__(self, weights: LossWeights) -> None:
        self.weights = weights

    @classmethod
    def from_config(cls, config_weights: Dict[str, float]) -> "LossEngine":
        return cls(
            LossWeights(
                alpha=float(config_weights.get("emotion", 1.0)),
                beta=float(config_weights.get("psychoacoustic", 1.0)),
                gamma=float(config_weights.get("coherence", 1.0)),
                delta=float(config_weights.get("economic", 1.0)),
                epsilon=float(config_weights.get("legal", 1.0)),
                zeta=float(config_weights.get("topology", 1.0)),
            )
        )

    def compute_total(
        self,
        l_emotion: float,
        l_psychoacoustic: float,
        l_coherence: float,
        l_economic: float,
        l_legal: float,
        l_topology: float,
    ) -> float:
        """L_total = aLe + bLp + gLc + dLeco + eLleg + zLtop."""

        w = self.weights
        return (
            w.alpha * l_emotion
            + w.beta * l_psychoacoustic
            + w.gamma * l_coherence
            + w.delta * l_economic
            + w.epsilon * l_legal
            + w.zeta * l_topology
        )

    def breakdown(
        self,
        l_emotion: float,
        l_psychoacoustic: float,
        l_coherence: float,
        l_economic: float,
        l_legal: float,
        l_topology: float,
    ) -> Dict[str, float]:
        total = self.compute_total(
            l_emotion,
            l_psychoacoustic,
            l_coherence,
            l_economic,
            l_legal,
            l_topology,
        )
        return {
            "emotion": l_emotion,
            "psychoacoustic": l_psychoacoustic,
            "coherence": l_coherence,
            "economic": l_economic,
            "legal": l_legal,
            "topology": l_topology,
            "total": total,
        }
