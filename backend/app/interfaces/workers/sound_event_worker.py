import asyncio
import logging
from datetime import UTC, datetime

from app.application.audio.use_cases import (
    ExecuteDueSoundEventsCommand,
    ExecuteDueSoundEventsUseCase,
)

logger = logging.getLogger(__name__)


class SoundEventWorker:
    def __init__(
        self,
        use_case: ExecuteDueSoundEventsUseCase,
        interval_seconds: float = 2.0,
    ) -> None:
        self._use_case = use_case
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _run_loop(self) -> None:
        while True:
            try:
                await self._use_case(ExecuteDueSoundEventsCommand(up_to=datetime.now(UTC)))
            except Exception:
                logger.exception("sound event worker iteration failed")
            await asyncio.sleep(self._interval_seconds)
