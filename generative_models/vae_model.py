"""Variational autoencoder with topology-aware penalty support."""
from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple


class TopologicalVAE:
    """Compact VAE for latent reconstruction and regularized generation."""

    def __init__(self, input_dim: int = 128, latent_dim: int = 32, seed: int = 41) -> None:
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.rng = random.Random(seed)

        self.enc_mu = [[self.rng.uniform(-0.08, 0.08) for _ in range(latent_dim)] for _ in range(input_dim)]
        self.enc_logvar = [[self.rng.uniform(-0.05, 0.05) for _ in range(latent_dim)] for _ in range(input_dim)]
        self.dec = [[self.rng.uniform(-0.08, 0.08) for _ in range(input_dim)] for _ in range(latent_dim)]
        self.dec_bias = [0.0 for _ in range(input_dim)]

    def _matvec(self, vector: Sequence[float], matrix: Sequence[Sequence[float]]) -> List[float]:
        out_dim = len(matrix[0]) if matrix else 0
        out = [0.0] * out_dim
        for j in range(out_dim):
            acc = 0.0
            for i in range(len(vector)):
                acc += vector[i] * matrix[i][j]
            out[j] = acc
        return out

    def encode(self, x: Sequence[float]) -> Tuple[List[float], List[float]]:
        if len(x) != self.input_dim:
            raise ValueError("Invalid input dimension")
        mu = self._matvec(x, self.enc_mu)
        logvar = self._matvec(x, self.enc_logvar)
        return mu, logvar

    def reparameterize(self, mu: Sequence[float], logvar: Sequence[float]) -> List[float]:
        z: List[float] = []
        for i in range(self.latent_dim):
            eps = self.rng.gauss(0.0, 1.0)
            sigma = math.exp(0.5 * logvar[i])
            z.append(mu[i] + sigma * eps)
        return z

    def decode(self, z: Sequence[float]) -> List[float]:
        out = self._matvec(z, self.dec)
        return [out[i] + self.dec_bias[i] for i in range(self.input_dim)]

    def forward(self, x: Sequence[float]) -> Dict[str, List[float]]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return {"mu": mu, "logvar": logvar, "z": z, "reconstruction": recon}

    def loss(
        self,
        x: Sequence[float],
        reconstruction: Sequence[float],
        mu: Sequence[float],
        logvar: Sequence[float],
        topology_penalty: float = 0.0,
    ) -> float:
        recon = sum((reconstruction[i] - x[i]) ** 2 for i in range(self.input_dim)) / self.input_dim
        kl = 0.0
        for i in range(self.latent_dim):
            kl += -0.5 * (1 + logvar[i] - mu[i] * mu[i] - math.exp(logvar[i]))
        kl /= self.latent_dim
        return recon + 0.1 * kl + topology_penalty

    def train_step(self, x: Sequence[float], lr: float = 1e-3, topology_penalty: float = 0.0) -> float:
        """Performs one optimization step on decoder/encoder mean heads."""

        out = self.forward(x)
        mu = out["mu"]
        logvar = out["logvar"]
        z = out["z"]
        recon = out["reconstruction"]
        loss = self.loss(x, recon, mu, logvar, topology_penalty=topology_penalty)

        recon_grad = [(2.0 / self.input_dim) * (recon[i] - x[i]) for i in range(self.input_dim)]

        for i in range(self.latent_dim):
            for j in range(self.input_dim):
                self.dec[i][j] -= lr * z[i] * recon_grad[j]
        for j in range(self.input_dim):
            self.dec_bias[j] -= lr * recon_grad[j]

        latent_grad = [sum(recon_grad[j] * self.dec[i][j] for j in range(self.input_dim)) for i in range(self.latent_dim)]
        for i in range(self.input_dim):
            xi = x[i]
            for j in range(self.latent_dim):
                self.enc_mu[i][j] -= lr * xi * latent_grad[j] * 0.1

        return loss
