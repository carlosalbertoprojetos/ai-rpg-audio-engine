"""Riemannian emotional field and stability utilities."""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt
from typing import Iterable, List, Sequence, Tuple


Vector = List[float]
Matrix = List[List[float]]


@dataclass
class EmotionalManifold:
    """Riemannian manifold over an emotional state vector."""

    dimension: int
    curvature_gain: float = 0.15

    def _validate(self, vector: Sequence[float]) -> None:
        if len(vector) != self.dimension:
            raise ValueError(f"Expected vector dimension {self.dimension}, got {len(vector)}")

    def metric_tensor(self, emotion: Sequence[float]) -> Matrix:
        """Compute g(E), a positive-definite metric tensor over emotional coordinates."""

        self._validate(emotion)
        metric: Matrix = []
        for i in range(self.dimension):
            row: List[float] = []
            for j in range(self.dimension):
                if i == j:
                    value = 1.0 + self.curvature_gain * abs(emotion[i])
                else:
                    value = 0.04 * exp(-abs(emotion[i] - emotion[j]))
                row.append(value)
            metric.append(row)
        return metric

    def _quad_form(self, metric: Matrix, delta: Sequence[float]) -> float:
        total = 0.0
        for i in range(self.dimension):
            for j in range(self.dimension):
                total += delta[i] * metric[i][j] * delta[j]
        return total

    def geodesic_distance(
        self,
        start: Sequence[float],
        end: Sequence[float],
        steps: int = 32,
    ) -> float:
        """Approximate geodesic distance by integrating local metric norm over a straight path."""

        self._validate(start)
        self._validate(end)

        delta = [end[i] - start[i] for i in range(self.dimension)]
        if all(abs(v) < 1e-12 for v in delta):
            return 0.0

        integral = 0.0
        for step in range(steps + 1):
            t = step / steps
            point = [start[i] + t * delta[i] for i in range(self.dimension)]
            g = self.metric_tensor(point)
            speed = sqrt(max(self._quad_form(g, delta), 0.0))
            weight = 0.5 if step in (0, steps) else 1.0
            integral += weight * speed
        return integral / steps

    def vector_field(
        self,
        emotion: Sequence[float],
        audio_drive: Sequence[float],
        collective_drive: Sequence[float],
        lambda_stability: float,
        kappa_collective: float,
    ) -> Vector:
        """Compute F(E, A, U) = -lambda*E + A + kappa*U."""

        self._validate(emotion)
        self._validate(audio_drive)
        self._validate(collective_drive)
        return [
            (-lambda_stability * emotion[i]) + audio_drive[i] + (kappa_collective * collective_drive[i])
            for i in range(self.dimension)
        ]

    def differential_step(
        self,
        emotion: Sequence[float],
        audio_drive: Sequence[float],
        collective_drive: Sequence[float],
        lambda_stability: float,
        kappa_collective: float,
        dt: float,
    ) -> Vector:
        """Single Euler step of dE/dt = F(E, A, U)."""

        field = self.vector_field(
            emotion=emotion,
            audio_drive=audio_drive,
            collective_drive=collective_drive,
            lambda_stability=lambda_stability,
            kappa_collective=kappa_collective,
        )
        return [emotion[i] + dt * field[i] for i in range(self.dimension)]

    def lyapunov(self, emotion: Sequence[float], target: Sequence[float] | None = None) -> float:
        """Lyapunov candidate V(E) = 1/2 * d_g(E, E*)^2."""

        self._validate(emotion)
        equilibrium = [0.0] * self.dimension if target is None else list(target)
        self._validate(equilibrium)
        distance = self.geodesic_distance(emotion, equilibrium)
        return 0.5 * distance * distance

    def check_stability(self, lambda_stability: float, kappa_collective: float) -> Tuple[bool, float]:
        """Stability criterion based on contraction dominance: lambda > kappa."""

        margin = float(lambda_stability - kappa_collective)
        return margin > 0.0, margin

    def simulate(
        self,
        initial_state: Sequence[float],
        audio_drive: Sequence[float],
        collective_drive: Sequence[float],
        lambda_stability: float,
        kappa_collective: float,
        dt: float,
        steps: int,
    ) -> List[Vector]:
        """Simulate emotional trajectory for numerical stability studies."""

        state = list(initial_state)
        self._validate(state)
        trajectory: List[Vector] = [state[:]]
        for _ in range(steps):
            state = self.differential_step(
                emotion=state,
                audio_drive=audio_drive,
                collective_drive=collective_drive,
                lambda_stability=lambda_stability,
                kappa_collective=kappa_collective,
                dt=dt,
            )
            trajectory.append(state[:])
        return trajectory


def l2_norm(vector: Iterable[float]) -> float:
    """Compute Euclidean norm."""

    return sqrt(sum(v * v for v in vector))
