from datetime import datetime
from typing import Protocol

from app.domain.audio.entities import SoundEvent
from app.domain.governance.entities import AuditLog
from app.domain.tableops.entities import Table


class TableRepository(Protocol):
    async def save(self, table: Table) -> None: ...

    async def get_by_id(self, table_id: str) -> Table | None: ...


class SoundEventRepository(Protocol):
    async def save(self, sound_event: SoundEvent) -> None: ...

    async def list_due(self, up_to: datetime) -> list[SoundEvent]: ...


class AuditLogRepository(Protocol):
    async def save(self, entry: AuditLog) -> None: ...

    async def list_by_organization(self, organization_id: str) -> list[AuditLog]: ...

