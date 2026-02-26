from dataclasses import dataclass
from typing import Any

from app.application.ports.repositories import AuditLogRepository
from app.domain.governance.entities import AuditLog


@dataclass(slots=True, frozen=True)
class RecordAuditEventCommand:
    organization_id: str
    action: str
    target: str
    data: dict[str, Any]
    actor_id: str | None = None


class RecordAuditEventUseCase:
    def __init__(self, audit_repository: AuditLogRepository) -> None:
        self._audit_repository = audit_repository

    async def __call__(self, command: RecordAuditEventCommand) -> AuditLog:
        entry = AuditLog.create(
            organization_id=command.organization_id,
            action=command.action,
            target=command.target,
            data=command.data,
            actor_id=command.actor_id,
        )
        await self._audit_repository.save(entry)
        return entry

