from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class AuditLog:
    id: str
    organization_id: str
    actor_id: str | None
    action: str
    target: str
    data: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        organization_id: str,
        action: str,
        target: str,
        data: dict[str, Any],
        actor_id: str | None = None,
    ) -> "AuditLog":
        return cls(
            id=str(uuid4()),
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            target=target,
            data=data,
        )

