import json
from collections import defaultdict

from fastapi import WebSocket

from app.domain.shared.events import DomainEvent


class TableSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, table_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[table_id].add(websocket)

    async def disconnect(self, table_id: str, websocket: WebSocket) -> None:
        if table_id in self._connections:
            self._connections[table_id].discard(websocket)
            if not self._connections[table_id]:
                del self._connections[table_id]

    async def broadcast_event(self, event: DomainEvent) -> None:
        table_id = str(event.payload.get("table_id", ""))
        if not table_id:
            return
        clients = list(self._connections.get(table_id, set()))
        data = json.dumps(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "payload": event.payload,
            },
            ensure_ascii=True,
        )
        stale: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_text(data)
            except Exception:
                stale.append(client)
        for client in stale:
            await self.disconnect(table_id, client)

