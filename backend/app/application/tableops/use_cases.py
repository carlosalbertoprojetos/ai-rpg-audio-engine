from dataclasses import dataclass

from app.application.governance.use_cases import RecordAuditEventCommand, RecordAuditEventUseCase
from app.application.ports.event_bus import EventBus
from app.application.ports.repositories import TableRepository
from app.domain.shared.events import DomainEvent
from app.domain.tableops.entities import Player, PlayerAvailability, Table


@dataclass(slots=True, frozen=True)
class CreateTableCommand:
    organization_id: str
    name: str
    actor_id: str | None = None


@dataclass(slots=True, frozen=True)
class AddPlayerCommand:
    organization_id: str
    table_id: str
    display_name: str
    user_id: str | None = None
    actor_id: str | None = None


@dataclass(slots=True, frozen=True)
class UpdatePlayerAvailabilityCommand:
    organization_id: str
    table_id: str
    player_id: str
    availability: PlayerAvailability
    actor_id: str | None = None


class CreateTableUseCase:
    def __init__(
        self,
        table_repository: TableRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._table_repository = table_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: CreateTableCommand) -> Table:
        table = Table.create(organization_id=command.organization_id, name=command.name)
        await self._table_repository.save(table)

        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                action="table.created",
                target=table.id,
                actor_id=command.actor_id,
                data={"name": table.name},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="table.created",
                payload={"table_id": table.id, "organization_id": command.organization_id},
            )
        )
        return table


class AddPlayerUseCase:
    def __init__(
        self,
        table_repository: TableRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._table_repository = table_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: AddPlayerCommand) -> Player:
        table = await self._table_repository.get_by_id(command.table_id)
        if table is None:
            raise ValueError("table not found")
        if table.organization_id != command.organization_id:
            raise ValueError("organization scope mismatch")

        player = Player.create(display_name=command.display_name, user_id=command.user_id)
        table.add_player(player)
        await self._table_repository.save(table)

        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                action="player.added",
                target=table.id,
                actor_id=command.actor_id,
                data={"player_id": player.id, "display_name": player.display_name},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="player.added",
                payload={
                    "table_id": table.id,
                    "player_id": player.id,
                    "display_name": player.display_name,
                    "availability": player.availability.value,
                },
            )
        )
        return player


class UpdatePlayerAvailabilityUseCase:
    def __init__(
        self,
        table_repository: TableRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._table_repository = table_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: UpdatePlayerAvailabilityCommand) -> Player:
        table = await self._table_repository.get_by_id(command.table_id)
        if table is None:
            raise ValueError("table not found")
        if table.organization_id != command.organization_id:
            raise ValueError("organization scope mismatch")
        player = table.update_player_availability(command.player_id, command.availability)
        await self._table_repository.save(table)

        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                action="player.availability.updated",
                target=table.id,
                actor_id=command.actor_id,
                data={"player_id": player.id, "availability": player.availability.value},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="player.availability.updated",
                payload={
                    "table_id": table.id,
                    "player_id": player.id,
                    "availability": player.availability.value,
                },
            )
        )
        return player
