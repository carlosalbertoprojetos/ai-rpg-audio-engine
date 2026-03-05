"""Topological consistency metrics for emotional embedding mappings."""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple


def _euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(min(len(a), len(b)))))


def pairwise_distances(points: Sequence[Sequence[float]]) -> List[float]:
    distances: List[float] = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distances.append(_euclidean(points[i], points[j]))
    return distances


def distortion_metric(original: Sequence[float], mapped: Sequence[float]) -> float:
    """Average relative distance distortion between two metric spaces."""

    if len(original) != len(mapped):
        raise ValueError("Distance vectors must have same size")
    if not original:
        return 0.0

    err = 0.0
    for o, m in zip(original, mapped):
        base = max(abs(o), 1e-8)
        err += abs(m - o) / base
    return err / len(original)


class TopologyPreserver:
    """Evaluates how much geometry is preserved after emotional mapping."""

    def preservation_score(
        self,
        source_vectors: Sequence[Sequence[float]],
        mapped_vectors: Sequence[Sequence[float]],
    ) -> float:
        """Returns score in [0, 1], where 1 means near-perfect distance preservation."""

        src_dist = pairwise_distances(source_vectors)
        dst_dist = pairwise_distances(mapped_vectors)
        distortion = distortion_metric(src_dist, dst_dist)
        return max(0.0, 1.0 - distortion)

    def evaluate(
        self,
        source_vectors: Sequence[Sequence[float]],
        mapped_vectors: Sequence[Sequence[float]],
    ) -> Tuple[float, float]:
        """Return preservation score and raw distortion value."""

        src_dist = pairwise_distances(source_vectors)
        dst_dist = pairwise_distances(mapped_vectors)
        distortion = distortion_metric(src_dist, dst_dist)
        return max(0.0, 1.0 - distortion), distortion
