from core_math.emotional_field import EmotionalManifold
from temporal_dynamics.trainer import TemporalTrainer
from temporal_dynamics.transformer_model import TemporalTransformer


def test_temporal_output_dimensions() -> None:
    model = TemporalTransformer(input_dim=5, model_dim=64, num_layers=6, num_heads=8)
    seq = [[0.1, -0.1, 0.2, -0.2, 0.0] for _ in range(6)]

    out = model.forward(seq)

    assert len(out) == len(seq)
    assert all(len(frame) == 5 for frame in out)


def test_temporal_smoothness_loss_prefers_smooth_sequences() -> None:
    model = TemporalTransformer(input_dim=5, model_dim=64, num_layers=6, num_heads=8)
    trainer = TemporalTrainer(model)

    smooth = [[0.1 * i] * 5 for i in range(8)]
    jagged = [[(-1.0 if i % 2 else 1.0)] * 5 for i in range(8)]

    assert trainer.smoothness_loss(smooth) < trainer.smoothness_loss(jagged)


def test_temporal_training_step_runs() -> None:
    model = TemporalTransformer(input_dim=5, model_dim=64, num_layers=6, num_heads=8)
    trainer = TemporalTrainer(model)
    manifold = EmotionalManifold(dimension=5)

    sequence = [[0.2, -0.1, 0.1, -0.05, 0.03] for _ in range(5)]
    loss = trainer.train_step(sequence, sequence, manifold, lr=1e-4)

    assert loss >= 0.0
