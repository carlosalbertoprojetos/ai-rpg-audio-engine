import math

from psychoacoustic_encoder.feature_extractor import PsychoacousticFeatureExtractor
from psychoacoustic_encoder.model import ResidualCNNEncoder


def _signal(length: int = 1024) -> list[float]:
    return [
        0.7 * math.sin(2 * math.pi * 220 * t / 16000)
        + 0.2 * math.sin(2 * math.pi * 330 * t / 16000)
        for t in range(length)
    ]


def test_encoder_output_shape_128d() -> None:
    extractor = PsychoacousticFeatureExtractor()
    model = ResidualCNNEncoder(embedding_dim=128)

    features = extractor.extract(_signal())
    embedding = model.forward(features)

    assert len(embedding) == 128


def test_encoder_backprop_functional() -> None:
    extractor = PsychoacousticFeatureExtractor()
    model = ResidualCNNEncoder(embedding_dim=128)

    features = extractor.extract(_signal())
    target = [0.0] * 128

    initial_loss = model.train_step(features, target, lr=0.002)
    loss = initial_loss
    for _ in range(12):
        loss = model.train_step(features, target, lr=0.002)

    assert loss < initial_loss
