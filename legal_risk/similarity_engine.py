"""Legal risk controls based on embedding similarity."""
from __future__ import annotations

import math
from typing import Dict, Sequence


class SimilarityEngine:
    """Computes similarity risk and applies automatic legal penalties."""

    def __init__(self, threshold: float = 0.9, penalty_scale: float = 10.0) -> None:
        self.threshold = threshold
        self.penalty_scale = penalty_scale

    def cosine_similarity(self, a: Sequence[float], b: Sequence[float]) -> float:
        if len(a) != len(b):
            raise ValueError("Vectors must have same size")
        dot = sum(a[i] * b[i] for i in range(len(a)))
        na = math.sqrt(sum(v * v for v in a))
        nb = math.sqrt(sum(v * v for v in b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def evaluate_risk(self, candidate: Sequence[float], reference: Sequence[float]) -> Dict[str, float | bool]:
        sim = self.cosine_similarity(candidate, reference)
        violation = sim >= self.threshold
        overflow = max(0.0, sim - self.threshold)
        penalty = overflow * self.penalty_scale
        return {
            "similarity": sim,
            "violation": violation,
            "penalty": penalty,
        }
