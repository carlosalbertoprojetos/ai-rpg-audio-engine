"""Conditioned diffusion model with cross-attention control."""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence


class ConditionedDiffusionModel:
    """Generative diffusion model conditioned on emotional vectors."""

    def __init__(self, latent_dim: int = 128, condition_dim: int = 5, steps: int = 8, seed: int = 31) -> None:
        self.latent_dim = latent_dim
        self.condition_dim = condition_dim
        self.steps = steps
        self.rng = random.Random(seed)
        self.cond_proj = [
            [self.rng.uniform(-0.12, 0.12) for _ in range(condition_dim)]
            for _ in range(latent_dim)
        ]

    def _softmax(self, values: Sequence[float]) -> List[float]:
        m = max(values)
        ex = [math.exp(v - m) for v in values]
        s = sum(ex) or 1.0
        return [e / s for e in ex]

    def cross_attention(self, latent: Sequence[float], condition: Sequence[float]) -> List[float]:
        """Project condition signal into latent space through attention weights."""

        if len(condition) != self.condition_dim:
            raise ValueError("Invalid condition dimension")

        context: List[float] = []
        for i in range(self.latent_dim):
            scores = [latent[i] * self.cond_proj[i][j] * condition[j] for j in range(self.condition_dim)]
            weights = self._softmax(scores)
            context.append(sum(weights[j] * condition[j] for j in range(self.condition_dim)))
        return context

    def denoise_step(self, latent: Sequence[float], condition: Sequence[float], step_index: int) -> List[float]:
        beta_t = 0.12 / (step_index + 1)
        context = self.cross_attention(latent, condition)
        return [(1.0 - beta_t) * latent[i] + beta_t * context[i] for i in range(self.latent_dim)]

    def sample(self, condition: Sequence[float], seed_latent: Sequence[float] | None = None) -> List[float]:
        """Generate conditioned latent representation via iterative denoising."""

        if seed_latent is None:
            latent = [self.rng.uniform(-1.0, 1.0) for _ in range(self.latent_dim)]
        else:
            if len(seed_latent) != self.latent_dim:
                raise ValueError("Invalid latent seed dimension")
            latent = [float(v) for v in seed_latent]

        for step in range(self.steps):
            latent = self.denoise_step(latent, condition, step)
        return latent

    def loss_components(
        self,
        generated: Sequence[float],
        target: Sequence[float],
        generated_emotion: Sequence[float],
        target_emotion: Sequence[float],
        generated_topology: float,
        target_topology: float,
    ) -> Dict[str, float]:
        """Compute spectral, emotional, and topological terms for conditioned generation."""

        if len(generated) != len(target):
            raise ValueError("Generated and target vectors must match")

        spectral = 0.0
        for i in range(1, len(generated)):
            dg = generated[i] - generated[i - 1]
            dt = target[i] - target[i - 1]
            spectral += (dg - dt) ** 2
        spectral /= max(len(generated) - 1, 1)

        emotional = sum((generated_emotion[i] - target_emotion[i]) ** 2 for i in range(min(len(generated_emotion), len(target_emotion))))
        emotional /= max(min(len(generated_emotion), len(target_emotion)), 1)

        topological = (generated_topology - target_topology) ** 2

        return {
            "spectral": spectral,
            "emotional": emotional,
            "topological": topological,
        }
