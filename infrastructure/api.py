"""Infrastructure API for generation and analysis endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from orchestrator.system_orchestrator import build_orchestrator
from psychoacoustic_encoder.model import flatten_features

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None  # type: ignore


@dataclass
class GenerateRequest:
    """Input payload for conditioned generation."""

    emotion: List[float]


@dataclass
class AnalyzeRequest:
    """Input payload for psychoacoustic analysis."""

    signal: List[float]


def _build_services() -> Dict[str, object]:
    orchestrator = build_orchestrator()
    return orchestrator.bootstrap()


_services = _build_services()


def health() -> Dict[str, str]:
    return {"status": "ok"}


def analyze(payload: AnalyzeRequest) -> Dict[str, object]:
    extractor = _services["extractor"]
    encoder = _services["encoder"]
    mapper = _services["mapper"]

    features = extractor.extract(payload.signal)
    embedding = encoder.forward(features)
    emotion = mapper.forward(embedding)

    return {
        "feature_keys": sorted(features.keys()),
        "embedding_dim": len(embedding),
        "emotion": emotion,
    }


def generate(payload: GenerateRequest) -> Dict[str, object]:
    diffusion = _services["diffusion"]
    latent = diffusion.sample(payload.emotion)
    return {
        "latent_dim": len(latent),
        "preview": latent[:8],
    }


if FastAPI is not None:
    app = FastAPI(title="Autonomous Auditory Emotional Engineering API")

    @app.get("/health")
    def health_endpoint() -> Dict[str, str]:
        return health()

    @app.post("/analyze")
    def analyze_endpoint(payload: Dict[str, List[float]]) -> Dict[str, object]:
        return analyze(AnalyzeRequest(signal=payload.get("signal", [])))

    @app.post("/generate")
    def generate_endpoint(payload: Dict[str, List[float]]) -> Dict[str, object]:
        return generate(GenerateRequest(emotion=payload.get("emotion", [0.0] * 5)))
else:  # pragma: no cover
    class _FallbackApp:
        """Fallback object when FastAPI is unavailable in runtime."""

        def __init__(self) -> None:
            self.routes: Dict[str, object] = {}

        def get(self, path: str):
            def decorator(fn):
                self.routes[f"GET {path}"] = fn
                return fn

            return decorator

        def post(self, path: str):
            def decorator(fn):
                self.routes[f"POST {path}"] = fn
                return fn

            return decorator

    app = _FallbackApp()
    app.routes["GET /health"] = health
    app.routes["POST /analyze"] = analyze
    app.routes["POST /generate"] = generate
