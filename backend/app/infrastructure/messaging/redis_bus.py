import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime

from redis.asyncio import Redis

from app.application.ports.event_bus import EventBus, EventHandler
from app.domain.shared.events import DomainEvent

logger = logging.getLogger(__name__)


class RedisEventBus(EventBus):
    def __init__(self, redis_client: Redis, channel_prefix: str = "rpgsounddesk") -> None:
        self._redis = redis_client
        self._channel_prefix = channel_prefix
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._seen_ids: set[str] = set()
        self._subscriber_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._subscriber_task is not None:
            return
        self._subscriber_task = asyncio.create_task(self._subscriber_loop())

    async def stop(self) -> None:
        if self._subscriber_task is not None:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
            self._subscriber_task = None
        await self._redis.close()

    async def publish(self, event: DomainEvent) -> None:
        await self._dispatch_local(event)
        channel = f"{self._channel_prefix}:{event.event_type}"
        await self._redis.publish(
            channel,
            json.dumps(
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "occurred_at": event.occurred_at.isoformat(),
                },
                ensure_ascii=True,
            ),
        )

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def _dispatch_local(self, event: DomainEvent) -> None:
        if event.event_id in self._seen_ids:
            return
        self._seen_ids.add(event.event_id)
        handlers = [*self._handlers.get(event.event_type, []), *self._handlers.get("*", [])]
        for handler in handlers:
            await handler(event)

    async def _subscriber_loop(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe(f"{self._channel_prefix}:*")
        try:
            async for message in pubsub.listen():
                if message["type"] not in {"message", "pmessage"}:
                    continue
                raw = message["data"]
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                try:
                    parsed = json.loads(raw)
                    event = DomainEvent(
                        event_type=str(parsed["event_type"]),
                        payload=dict(parsed["payload"]),
                        event_id=str(parsed["event_id"]),
                        occurred_at=datetime.fromisoformat(str(parsed["occurred_at"])).astimezone(UTC),
                    )
                    await self._dispatch_local(event)
                except Exception:
                    logger.exception("failed to process redis event")
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.close()

