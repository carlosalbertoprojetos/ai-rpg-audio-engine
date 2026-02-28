from dataclasses import dataclass

from app.application.governance.use_cases import RecordAuditEventCommand, RecordAuditEventUseCase
from app.application.ports.enterprise import SessionRepository
from app.application.ports.event_bus import EventBus
from app.application.ports.repositories import TableRepository
from app.domain.shared.events import DomainEvent
from app.domain.tableops.entities import Session, SessionState


@dataclass(slots=True, frozen=True)
class StartSessionCommand:
    organization_id: str
    table_id: str
    actor_id: str


@dataclass(slots=True, frozen=True)
class EndSessionCommand:
    organization_id: str
    session_id: str
    actor_id: str


class StartSessionUseCase:
    def __init__(
        self,
        table_repository: TableRepository,
        session_repository: SessionRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._table_repository = table_repository
        self._session_repository = session_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: StartSessionCommand) -> Session:
        table = await self._table_repository.get_by_id(command.table_id)
        if table is None:
            raise ValueError("table not found")
        if table.organization_id != command.organization_id:
            raise ValueError("organization scope mismatch")

        running = await self._session_repository.get_running_by_table(command.table_id)
        if running is not None:
            return running

        session = Session.start(table_id=command.table_id)
        await self._session_repository.save(session)

        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action="session.started",
                target=session.id,
                data={"table_id": command.table_id},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="session.started",
                payload={"table_id": command.table_id, "session_id": session.id},
            )
        )
        return session


class EndSessionUseCase:
    def __init__(
        self,
        session_repository: SessionRepository,
        table_repository: TableRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._session_repository = session_repository
        self._table_repository = table_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: EndSessionCommand) -> Session:
        session = await self._session_repository.get_by_id(command.session_id)
        if session is None:
            raise ValueError("session not found")
        table = await self._table_repository.get_by_id(session.table_id)
        if table is None:
            raise ValueError("table not found")
        if table.organization_id != command.organization_id:
            raise ValueError("organization scope mismatch")

        if session.state == SessionState.RUNNING:
            session.finish()
            await self._session_repository.save(session)
            await self._event_bus.publish(
                DomainEvent(
                    event_type="session.ended",
                    payload={"table_id": session.table_id, "session_id": session.id},
                )
            )
            await self._record_audit(
                RecordAuditEventCommand(
                    organization_id=command.organization_id,
                    actor_id=command.actor_id,
                    action="session.ended",
                    target=session.id,
                    data={"table_id": session.table_id},
                )
            )
        return session

