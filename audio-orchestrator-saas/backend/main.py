"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes_audio import router as audio_router
from backend.api.routes_generation import router as generation_router
from backend.config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(audio_router, prefix=settings.api_prefix)
    app.include_router(generation_router, prefix=settings.api_prefix)
    return app


app = create_app()
