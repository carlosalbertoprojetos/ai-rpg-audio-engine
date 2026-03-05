"""Mapping from psychoacoustic embeddings to emotional manifold coordinates."""
from __future__ import annotations

import math
import random
from typing import List, Sequence

from core_math.emotional_field import EmotionalManifold


class EmotionalMapper:
    """MLP mapper with architecture 128 -> 256 -> 128 -> emotional_dim."""

    def __init__(self, input_dim: int = 128, emotional_dim: int = 5, seed: int = 13) -> None:
        self.input_dim = input_dim
        self.emotional_dim = emotional_dim
        self.rng = random.Random(seed)

        self.w1 = [[self.rng.uniform(-0.07, 0.07) for _ in range(256)] for _ in range(input_dim)]
        self.b1 = [0.0] * 256

        self.w2 = [[self.rng.uniform(-0.06, 0.06) for _ in range(128)] for _ in range(256)]
        self.b2 = [0.0] * 128

        self.w3 = [[self.rng.uniform(-0.05, 0.05) for _ in range(emotional_dim)] for _ in range(128)]
        self.b3 = [0.0] * emotional_dim

        # Dimension-specific normalization scales based on emotional semantics.
        self.norm_scales = [1.0, 0.9, 0.8, 1.1, 0.95][:emotional_dim]

    def _dense(self, vec: Sequence[float], weight: Sequence[Sequence[float]], bias: Sequence[float]) -> List[float]:
        out = [0.0] * len(bias)
        for j in range(len(bias)):
            acc = bias[j]
            for i in range(len(vec)):
                acc += vec[i] * weight[i][j]
            out[j] = acc
        return out

    def _relu(self, vec: Sequence[float]) -> List[float]:
        return [v if v > 0.0 else 0.0 for v in vec]

    def _tanh(self, vec: Sequence[float]) -> List[float]:
        return [math.tanh(v) for v in vec]

    def normalize_by_dimension(self, state: Sequence[float]) -> List[float]:
        """Apply per-dimension normalization to preserve stable emotional ranges."""

        if len(state) != self.emotional_dim:
            raise ValueError("Invalid emotional state dimension")
        return [state[i] * self.norm_scales[i] for i in range(self.emotional_dim)]

    def forward(self, embedding: Sequence[float]) -> List[float]:
        if len(embedding) != self.input_dim:
            raise ValueError(f"Expected embedding dim {self.input_dim}, got {len(embedding)}")

        h1 = self._relu(self._dense(embedding, self.w1, self.b1))
        h2 = self._relu(self._dense(h1, self.w2, self.b2))
        out = self._tanh(self._dense(h2, self.w3, self.b3))
        return self.normalize_by_dimension(out)

    def geodesic_loss(
        self,
        predicted: Sequence[float],
        target: Sequence[float],
        manifold: EmotionalManifold,
    ) -> float:
        """Geodesic loss on manifold plus Euclidean alignment for local smoothness."""

        if len(predicted) != self.emotional_dim or len(target) != self.emotional_dim:
            raise ValueError("Emotional vector dimension mismatch")

        d_geo = manifold.geodesic_distance(predicted, target)
        d_euclid = sum((predicted[i] - target[i]) ** 2 for i in range(self.emotional_dim)) / self.emotional_dim
        return d_geo + 0.25 * d_euclid

    def train_step(
        self,
        embedding: Sequence[float],
        target: Sequence[float],
        manifold: EmotionalManifold,
        lr: float = 1e-3,
    ) -> float:
        """Update the output layer using a local gradient approximation on geodesic loss."""

        pred = self.forward(embedding)
        loss = self.geodesic_loss(pred, target, manifold)

        grad = [(pred[i] - target[i]) * (2.0 / self.emotional_dim) for i in range(self.emotional_dim)]

        h1 = self._relu(self._dense(embedding, self.w1, self.b1))
        h2 = self._relu(self._dense(h1, self.w2, self.b2))
        for i in range(128):
            for j in range(self.emotional_dim):
                self.w3[i][j] -= lr * h2[i] * grad[j]
        for j in range(self.emotional_dim):
            self.b3[j] -= lr * grad[j]

        return loss
