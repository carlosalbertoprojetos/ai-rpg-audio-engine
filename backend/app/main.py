from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.container import Container, build_container
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.infrastructure.observability.otel import setup_opentelemetry
from app.interfaces.api.router import get_router
from app.interfaces.workers.sound_event_worker import SoundEventWorker


def create_app(
    settings: Settings | None = None,
    container_factory: Callable[[Settings], Container] = build_container,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await container.start()
        await worker.start()
        try:
            yield
        finally:
            await worker.stop()
            await container.stop()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    setup_opentelemetry(app, settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    container = container_factory(settings)
    worker = SoundEventWorker(
        use_case=container.use_cases.execute_due_sound_events,
        interval_seconds=settings.sound_event_poll_interval_seconds,
    )

    def get_container() -> Container:
        return container

    app.include_router(get_router(get_container), prefix=settings.api_prefix)
    return app


app = create_app()
