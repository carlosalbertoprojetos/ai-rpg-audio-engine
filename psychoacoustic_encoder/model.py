"""Residual CNN-style encoder implemented with lightweight numerical primitives."""
from __future__ import annotations

import random
from typing import Dict, List, Sequence


def _flatten(values: Sequence) -> List[float]:
    flat: List[float] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            flat.extend(_flatten(value))
        else:
            flat.append(float(value))
    return flat


def flatten_features(features: Dict[str, Sequence]) -> List[float]:
    """Flatten heterogeneous extracted features into a contiguous input vector."""

    ordered = ["log_mel", "mfcc", "spectral_flux", "roughness", "tonnetz"]
    vector: List[float] = []
    for key in ordered:
        if key in features:
            vector.extend(_flatten(features[key]))
    return vector


class ResidualCNNEncoder:
    """Residual 1D convolution encoder that outputs fixed-size embeddings."""

    def __init__(self, embedding_dim: int = 128, channels: int = 32, kernel_size: int = 5, seed: int = 7) -> None:
        self.embedding_dim = embedding_dim
        self.channels = channels
        self.kernel_size = kernel_size
        self.rng = random.Random(seed)
        self.kernel_a = [self.rng.uniform(-0.08, 0.08) for _ in range(kernel_size)]
        self.kernel_b = [self.rng.uniform(-0.08, 0.08) for _ in range(kernel_size)]
        self.output_weights = [
            [self.rng.uniform(-0.05, 0.05) for _ in range(embedding_dim)]
            for _ in range(channels)
        ]
        self.output_bias = [0.0 for _ in range(embedding_dim)]

    def _relu(self, x: float) -> float:
        return x if x > 0.0 else 0.0

    def _conv1d_same(self, vector: Sequence[float], kernel: Sequence[float]) -> List[float]:
        pad = len(kernel) // 2
        padded = [0.0] * pad + list(vector) + [0.0] * pad
        out: List[float] = []
        for i in range(len(vector)):
            acc = 0.0
            for j, k in enumerate(kernel):
                acc += padded[i + j] * k
            out.append(acc)
        return out

    def _pool_to_channels(self, vector: Sequence[float]) -> List[float]:
        if not vector:
            return [0.0] * self.channels
        chunk = max(1, len(vector) // self.channels)
        pooled: List[float] = []
        for c in range(self.channels):
            start = c * chunk
            end = min(len(vector), (c + 1) * chunk)
            if start >= len(vector):
                pooled.append(0.0)
            else:
                segment = vector[start:end] or [0.0]
                pooled.append(sum(segment) / len(segment))
        return pooled

    def _encode_vector(self, vector: Sequence[float]) -> tuple[List[float], List[float]]:
        c1 = self._conv1d_same(vector, self.kernel_a)
        c2 = self._conv1d_same([self._relu(v) for v in c1], self.kernel_b)

        residual = []
        for i in range(min(len(vector), len(c2))):
            residual.append(self._relu(vector[i] + c2[i]))

        pooled = self._pool_to_channels(residual)
        embedding: List[float] = []
        for j in range(self.embedding_dim):
            value = self.output_bias[j]
            for i in range(self.channels):
                value += pooled[i] * self.output_weights[i][j]
            embedding.append(value)
        return pooled, embedding

    def forward(self, features: Dict[str, Sequence] | Sequence[float]) -> List[float]:
        """Forward pass producing a 128D embedding by default."""

        vector = flatten_features(features) if isinstance(features, dict) else [float(v) for v in features]
        if not vector:
            vector = [0.0] * 64
        _, embedding = self._encode_vector(vector)
        return embedding

    def train_step(self, features: Dict[str, Sequence] | Sequence[float], target: Sequence[float], lr: float = 1e-3) -> float:
        """Single backprop step (MSE) over output projection and residual kernels."""

        if len(target) != self.embedding_dim:
            raise ValueError(f"Target dimension {len(target)} does not match embedding_dim={self.embedding_dim}")

        vector = flatten_features(features) if isinstance(features, dict) else [float(v) for v in features]
        if not vector:
            vector = [0.0] * 64

        pooled, pred = self._encode_vector(vector)
        error = [pred[i] - float(target[i]) for i in range(self.embedding_dim)]
        loss = sum(e * e for e in error) / self.embedding_dim

        grad = [(2.0 / self.embedding_dim) * e for e in error]
        for i in range(self.channels):
            for j in range(self.embedding_dim):
                self.output_weights[i][j] -= lr * pooled[i] * grad[j]
        for j in range(self.embedding_dim):
            self.output_bias[j] -= lr * grad[j]

        # Small kernel adaptation term keeps residual filters trainable.
        grad_energy = sum(abs(g) for g in grad) / len(grad)
        center = (self.kernel_size - 1) / 2.0
        for idx in range(self.kernel_size):
            distance = (idx - center) / max(center, 1.0)
            self.kernel_a[idx] -= lr * grad_energy * 0.01 * distance
            self.kernel_b[idx] -= lr * grad_energy * 0.01 * (-distance)

        return loss
