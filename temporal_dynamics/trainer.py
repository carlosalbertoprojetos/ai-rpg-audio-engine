"""Training support for temporal emotional dynamics."""
from __future__ import annotations

from typing import List, Sequence

from core_math.emotional_field import EmotionalManifold
from temporal_dynamics.transformer_model import TemporalTransformer


class TemporalTrainer:
    """Computes losses and performs lightweight parameter updates."""

    def __init__(self, model: TemporalTransformer, smoothness_weight: float = 0.3, stability_weight: float = 0.2) -> None:
        self.model = model
        self.smoothness_weight = smoothness_weight
        self.stability_weight = stability_weight

    def mse_loss(self, predicted: Sequence[Sequence[float]], target: Sequence[Sequence[float]]) -> float:
        if len(predicted) != len(target):
            raise ValueError("Predicted and target sequence sizes differ")
        if not predicted:
            return 0.0

        acc = 0.0
        count = 0
        for p, t in zip(predicted, target):
            for i in range(min(len(p), len(t))):
                diff = p[i] - t[i]
                acc += diff * diff
                count += 1
        return acc / max(count, 1)

    def smoothness_loss(self, sequence: Sequence[Sequence[float]]) -> float:
        """Penalize frame-to-frame acceleration for temporal continuity."""

        if len(sequence) < 3:
            return 0.0
        acc = 0.0
        count = 0
        for i in range(2, len(sequence)):
            for j in range(len(sequence[i])):
                second_derivative = sequence[i][j] - 2 * sequence[i - 1][j] + sequence[i - 2][j]
                acc += second_derivative * second_derivative
                count += 1
        return acc / max(count, 1)

    def stability_regularization(self, sequence: Sequence[Sequence[float]], manifold: EmotionalManifold) -> float:
        """Average Lyapunov energy over the predicted sequence."""

        if not sequence:
            return 0.0
        return sum(manifold.lyapunov(frame) for frame in sequence) / len(sequence)

    def total_loss(
        self,
        predicted: Sequence[Sequence[float]],
        target: Sequence[Sequence[float]],
        manifold: EmotionalManifold,
    ) -> float:
        recon = self.mse_loss(predicted, target)
        smooth = self.smoothness_loss(predicted)
        stable = self.stability_regularization(predicted, manifold)
        return recon + (self.smoothness_weight * smooth) + (self.stability_weight * stable)

    def train_step(
        self,
        input_sequence: Sequence[Sequence[float]],
        target_sequence: Sequence[Sequence[float]],
        manifold: EmotionalManifold,
        lr: float = 1e-4,
    ) -> float:
        """One optimization step on output projection weights using MSE gradients."""

        latent = self.model.encode(input_sequence)
        predicted = self.model.decode(latent)
        loss = self.total_loss(predicted, target_sequence, manifold)

        n_frames = max(len(predicted), 1)
        for t, (pred_frame, tgt_frame) in enumerate(zip(predicted, target_sequence)):
            grad_out = [2.0 * (pred_frame[j] - tgt_frame[j]) / n_frames for j in range(self.model.input_dim)]
            token = latent[t]
            for i in range(self.model.model_dim):
                for j in range(self.model.input_dim):
                    self.model.output_proj[i][j] -= lr * token[i] * grad_out[j]

        return loss
