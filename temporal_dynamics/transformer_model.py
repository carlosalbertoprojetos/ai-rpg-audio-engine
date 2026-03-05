"""Temporal transformer for emotional trajectory prediction."""
from __future__ import annotations

import math
import random
from typing import List, Sequence


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(a[i] * b[i] for i in range(min(len(a), len(b))))


def _matvec(vec: Sequence[float], matrix: Sequence[Sequence[float]]) -> List[float]:
    out_dim = len(matrix[0]) if matrix else 0
    out = [0.0] * out_dim
    for j in range(out_dim):
        acc = 0.0
        for i in range(len(vec)):
            acc += vec[i] * matrix[i][j]
        out[j] = acc
    return out


def _softmax(values: Sequence[float]) -> List[float]:
    if not values:
        return []
    m = max(values)
    expv = [math.exp(v - m) for v in values]
    s = sum(expv) or 1.0
    return [v / s for v in expv]


class TemporalTransformer:
    """Lightweight transformer with 6 layers and 8 attention heads."""

    def __init__(
        self,
        input_dim: int = 5,
        model_dim: int = 64,
        num_layers: int = 6,
        num_heads: int = 8,
        seed: int = 23,
    ) -> None:
        if model_dim % num_heads != 0:
            raise ValueError("model_dim must be divisible by num_heads")

        self.input_dim = input_dim
        self.model_dim = model_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = model_dim // num_heads
        self.rng = random.Random(seed)

        self.input_proj = [[self.rng.uniform(-0.08, 0.08) for _ in range(model_dim)] for _ in range(input_dim)]
        self.output_proj = [[self.rng.uniform(-0.08, 0.08) for _ in range(input_dim)] for _ in range(model_dim)]

        self.q_proj = self._init_layer_head_mats()
        self.k_proj = self._init_layer_head_mats()
        self.v_proj = self._init_layer_head_mats()
        self.ff1 = [self._rand_matrix(model_dim, model_dim) for _ in range(num_layers)]
        self.ff2 = [self._rand_matrix(model_dim, model_dim) for _ in range(num_layers)]

    def _rand_matrix(self, in_dim: int, out_dim: int) -> List[List[float]]:
        return [[self.rng.uniform(-0.05, 0.05) for _ in range(out_dim)] for _ in range(in_dim)]

    def _init_layer_head_mats(self) -> List[List[List[List[float]]]]:
        mats: List[List[List[List[float]]]] = []
        for _ in range(self.num_layers):
            head_mats: List[List[List[float]]] = []
            for _ in range(self.num_heads):
                head_mats.append(self._rand_matrix(self.model_dim, self.head_dim))
            mats.append(head_mats)
        return mats

    def positional_encoding(self, t: float) -> List[float]:
        """Continuous-time sinusoidal encoding."""

        enc = [0.0] * self.model_dim
        for i in range(0, self.model_dim, 2):
            freq = 1.0 / (10000 ** (i / self.model_dim))
            enc[i] = math.sin(t * freq)
            if i + 1 < self.model_dim:
                enc[i + 1] = math.cos(t * freq)
        return enc

    def _attention_layer(self, tokens: Sequence[Sequence[float]], layer_idx: int) -> List[List[float]]:
        n = len(tokens)
        if n == 0:
            return []
        attn_out = [[0.0] * self.model_dim for _ in range(n)]

        for head in range(self.num_heads):
            q = [_matvec(tok, self.q_proj[layer_idx][head]) for tok in tokens]
            k = [_matvec(tok, self.k_proj[layer_idx][head]) for tok in tokens]
            v = [_matvec(tok, self.v_proj[layer_idx][head]) for tok in tokens]

            for i in range(n):
                scores = [_dot(q[i], k[j]) / math.sqrt(self.head_dim) for j in range(n)]
                weights = _softmax(scores)
                context = [0.0] * self.head_dim
                for j in range(n):
                    for d in range(self.head_dim):
                        context[d] += weights[j] * v[j][d]

                offset = head * self.head_dim
                for d in range(self.head_dim):
                    attn_out[i][offset + d] = context[d]

        mixed: List[List[float]] = []
        for i in range(n):
            mixed.append([0.7 * tokens[i][d] + 0.3 * attn_out[i][d] for d in range(self.model_dim)])
        return mixed

    def _feed_forward_layer(self, tokens: Sequence[Sequence[float]], layer_idx: int) -> List[List[float]]:
        updated: List[List[float]] = []
        for token in tokens:
            h = _matvec(token, self.ff1[layer_idx])
            h = [v if v > 0.0 else 0.0 for v in h]
            y = _matvec(h, self.ff2[layer_idx])
            updated.append([0.8 * token[d] + 0.2 * y[d] for d in range(self.model_dim)])
        return updated

    def encode(self, sequence: Sequence[Sequence[float]], dt: float = 1.0) -> List[List[float]]:
        """Encode emotional sequence into latent temporal representation."""

        tokens: List[List[float]] = []
        for i, frame in enumerate(sequence):
            if len(frame) != self.input_dim:
                raise ValueError(f"Expected input dim {self.input_dim}, got {len(frame)}")
            token = _matvec(frame, self.input_proj)
            pos = self.positional_encoding(i * dt)
            tokens.append([token[d] + pos[d] for d in range(self.model_dim)])

        for layer_idx in range(self.num_layers):
            tokens = self._attention_layer(tokens, layer_idx)
            tokens = self._feed_forward_layer(tokens, layer_idx)
        return tokens

    def decode(self, latent_tokens: Sequence[Sequence[float]]) -> List[List[float]]:
        return [_matvec(token, self.output_proj) for token in latent_tokens]

    def forward(self, sequence: Sequence[Sequence[float]], dt: float = 1.0) -> List[List[float]]:
        """Predict the next-step emotional trajectory."""

        return self.decode(self.encode(sequence, dt=dt))
