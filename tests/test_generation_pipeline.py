from generative_models.diffusion_model import ConditionedDiffusionModel
from generative_models.vae_model import TopologicalVAE


def test_generation_pipeline_forward_backward() -> None:
    diffusion = ConditionedDiffusionModel(latent_dim=128, condition_dim=5)
    vae = TopologicalVAE(input_dim=128, latent_dim=32)

    condition = [0.2, -0.1, 0.15, -0.05, 0.1]
    generated = diffusion.sample(condition)
    out = vae.forward(generated)

    assert len(generated) == 128
    assert len(out["reconstruction"]) == 128

    initial_loss = vae.train_step(generated, lr=0.001)
    final_loss = vae.train_step(generated, lr=0.001)

    assert final_loss <= initial_loss * 1.1


def test_generation_losses_are_available() -> None:
    diffusion = ConditionedDiffusionModel(latent_dim=128, condition_dim=5)
    condition = [0.1, 0.0, -0.1, 0.2, -0.2]

    generated = diffusion.sample(condition)
    losses = diffusion.loss_components(
        generated=generated,
        target=generated,
        generated_emotion=condition,
        target_emotion=condition,
        generated_topology=0.3,
        target_topology=0.2,
    )

    assert set(losses.keys()) == {"spectral", "emotional", "topological"}
    assert losses["spectral"] >= 0.0
