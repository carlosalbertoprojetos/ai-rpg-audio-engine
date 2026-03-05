from collective_dynamics.collective_field import CollectiveField


def _dispersion(states: list[list[float]]) -> float:
    center = [sum(values) / len(values) for values in zip(*states)]
    total = 0.0
    for state in states:
        total += sum((state[i] - center[i]) ** 2 for i in range(len(center)))
    return total / len(states)


def test_collective_field_reduces_dispersion() -> None:
    field = CollectiveField(kappa=0.7)
    initial = [
        [0.9, -0.7, 0.5, -0.3, 0.2],
        [-0.8, 0.6, -0.4, 0.2, -0.1],
        [0.7, -0.5, 0.3, -0.1, 0.0],
    ]

    history = field.simulate_multiagent(initial, steps=50, lambda_stability=1.3, dt=0.05)

    assert _dispersion(history[-1]) < _dispersion(history[0])
