import pytest

from app.application.governance.use_cases import RecordAuditEventUseCase
from app.application.tableops.use_cases import (
    AddPlayerCommand,
    AddPlayerUseCase,
    CreateTableCommand,
    CreateTableUseCase,
)
from app.infrastructure.messaging.in_memory_bus import InMemoryEventBus
from app.infrastructure.repositories.in_memory import (
    InMemoryAuditLogRepository,
    InMemoryTableRepository,
)


@pytest.mark.asyncio
async def test_create_table_and_add_player() -> None:
    table_repository = InMemoryTableRepository()
    audit_repository = InMemoryAuditLogRepository()
    event_bus = InMemoryEventBus()
    record_audit = RecordAuditEventUseCase(audit_repository)

    create_table = CreateTableUseCase(table_repository, event_bus, record_audit)
    add_player = AddPlayerUseCase(table_repository, event_bus, record_audit)

    table = await create_table(CreateTableCommand(organization_id="org-1", name="Mesa Atlas"))
    player = await add_player(
        AddPlayerCommand(
            organization_id="org-1",
            table_id=table.id,
            display_name="Dorian",
        )
    )

    assert player.display_name == "Dorian"
    loaded = await table_repository.get_by_id(table.id)
    assert loaded is not None
    assert player.id in loaded.players

