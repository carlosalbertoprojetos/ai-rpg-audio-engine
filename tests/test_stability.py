from core_math.emotional_field import EmotionalManifold, l2_norm


def test_stability_margin_rule_lambda_gt_kappa() -> None:
    manifold = EmotionalManifold(dimension=5)
    stable, margin = manifold.check_stability(lambda_stability=1.2, kappa_collective=0.6)
    assert stable
    assert margin > 0.0


def test_numerical_convergence_under_stable_dynamics() -> None:
    manifold = EmotionalManifold(dimension=5)
    initial = [1.0, -0.8, 0.6, -0.4, 0.2]
    zeros = [0.0] * 5
    trajectory = manifold.simulate(
        initial_state=initial,
        audio_drive=zeros,
        collective_drive=zeros,
        lambda_stability=1.4,
        kappa_collective=0.5,
        dt=0.05,
        steps=120,
    )

    assert l2_norm(trajectory[-1]) < l2_norm(trajectory[0])
    assert manifold.lyapunov(trajectory[-1]) < manifold.lyapunov(trajectory[0])
