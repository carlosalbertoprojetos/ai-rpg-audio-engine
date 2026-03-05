"""Collective emotional dynamics for multi-agent coupling."""
from __future__ import annotations

from typing import List, Sequence


class CollectiveField:
    """Models coupled emotional dynamics across a group of agents."""

    def __init__(self, kappa: float = 0.6) -> None:
        self.kappa = kappa

    def weighted_mean(self, states: Sequence[Sequence[float]], weights: Sequence[float] | None = None) -> List[float]:
        if not states:
            return []
        dim = len(states[0])
        if weights is None:
            weights = [1.0] * len(states)
        if len(weights) != len(states):
            raise ValueError("Weights size mismatch")

        total_weight = sum(weights) or 1.0
        mean = [0.0] * dim
        for s, w in zip(states, weights):
            for i in range(dim):
                mean[i] += s[i] * w
        return [v / total_weight for v in mean]

    def coupled_update(
        self,
        state: Sequence[float],
        collective_target: Sequence[float],
        lambda_stability: float,
        dt: float,
    ) -> List[float]:
        """Euler step of coupled agent dynamics."""

        if len(state) != len(collective_target):
            raise ValueError("State and collective target dimensions must match")

        next_state: List[float] = []
        for i in range(len(state)):
            derivative = (-lambda_stability * state[i]) + (self.kappa * collective_target[i])
            next_state.append(state[i] + dt * derivative)
        return next_state

    def simulate_multiagent(
        self,
        initial_states: Sequence[Sequence[float]],
        steps: int,
        lambda_stability: float,
        dt: float = 0.1,
        weights: Sequence[float] | None = None,
    ) -> List[List[List[float]]]:
        """Simulate coupled emotional trajectories for all agents."""

        states = [list(s) for s in initial_states]
        history: List[List[List[float]]] = [[s[:] for s in states]]

        for _ in range(steps):
            center = self.weighted_mean(states, weights)
            states = [self.coupled_update(s, center, lambda_stability=lambda_stability, dt=dt) for s in states]
            history.append([s[:] for s in states])

        return history
