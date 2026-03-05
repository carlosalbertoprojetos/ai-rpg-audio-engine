"""Simplified Pareto optimizer for multiobjective balancing."""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


class ParetoOptimizer:
    """Finds non-dominated candidates and updates objective weights dynamically."""

    def __init__(self, min_weight: float = 0.05) -> None:
        self.min_weight = min_weight

    def adjust_dynamic_weights(self, recent_losses: Dict[str, float]) -> Dict[str, float]:
        """Increase focus on weak objectives via inverse-loss weighting."""

        if not recent_losses:
            return {}

        inv = {k: 1.0 / max(v, 1e-8) for k, v in recent_losses.items()}
        total = sum(inv.values()) or 1.0
        normalized = {k: max(self.min_weight, inv[k] / total) for k in inv}
        renorm = sum(normalized.values())
        return {k: normalized[k] / renorm for k in normalized}

    def _dominates(self, a: Sequence[float], b: Sequence[float]) -> bool:
        no_worse = all(a_i <= b_i for a_i, b_i in zip(a, b))
        strictly_better = any(a_i < b_i for a_i, b_i in zip(a, b))
        return no_worse and strictly_better

    def pareto_search(self, candidates: Sequence[Tuple[str, Sequence[float]]]) -> List[Tuple[str, Sequence[float]]]:
        """Return non-dominated front from candidate objective vectors (minimization)."""

        front: List[Tuple[str, Sequence[float]]] = []
        for name_a, vec_a in candidates:
            dominated = False
            for name_b, vec_b in candidates:
                if name_a == name_b:
                    continue
                if self._dominates(vec_b, vec_a):
                    dominated = True
                    break
            if not dominated:
                front.append((name_a, vec_a))
        return front
