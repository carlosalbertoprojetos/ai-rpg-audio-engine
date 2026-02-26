from datetime import UTC, datetime

from app.application.ports.repositories import (
    AuditLogRepository,
    SoundEventRepository,
    TableRepository,
)
from app.domain.audio.entities import SoundEvent
from app.domain.governance.entities import AuditLog
from app.domain.tableops.entities import Table


class InMemoryTableRepository(TableRepository):
    def __init__(self) -> None:
        self._items: dict[str, Table] = {}

    async def save(self, table: Table) -> None:
        self._items[table.id] = table

    async def get_by_id(self, table_id: str) -> Table | None:
        return self._items.get(table_id)


class InMemorySoundEventRepository(SoundEventRepository):
    def __init__(self) -> None:
        self._items: dict[str, SoundEvent] = {}

    async def save(self, sound_event: SoundEvent) -> None:
        self._items[sound_event.id] = sound_event

    async def list_due(self, up_to: datetime) -> list[SoundEvent]:
        utc_cutoff = up_to.astimezone(UTC)
        return [event for event in self._items.values() if event.execute_at <= utc_cutoff]


class InMemoryAuditLogRepository(AuditLogRepository):
    def __init__(self) -> None:
        self._items: list[AuditLog] = []

    async def save(self, entry: AuditLog) -> None:
        self._items.append(entry)

    async def list_by_organization(self, organization_id: str) -> list[AuditLog]:
        return [entry for entry in self._items if entry.organization_id == organization_id]

