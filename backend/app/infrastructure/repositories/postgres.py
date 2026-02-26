import asyncio
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.repositories import (
    AuditLogRepository,
    SoundEventRepository,
    TableRepository,
)
from app.domain.audio.entities import SoundEvent, SoundEventState
from app.domain.governance.entities import AuditLog
from app.domain.tableops.entities import Player, PlayerAvailability, Table
from app.infrastructure.db.models import AuditLogRecord, SoundEventRecord, TableRecord


def _to_table_domain(record: TableRecord) -> Table:
    table = Table(id=record.id, organization_id=record.organization_id, name=record.name)
    for player_id, payload in record.players.items():
        availability = PlayerAvailability(payload["availability"])
        table.players[player_id] = Player(
            id=player_id,
            display_name=payload["display_name"],
            availability=availability,
            user_id=payload.get("user_id") or None,
        )
    return table


def _to_table_record_payload(table: Table) -> dict[str, dict[str, str]]:
    return {
        player_id: {
            "display_name": player.display_name,
            "availability": player.availability.value,
            "user_id": player.user_id or "",
        }
        for player_id, player in table.players.items()
    }


def _to_sound_event_domain(record: SoundEventRecord) -> SoundEvent:
    return SoundEvent(
        id=record.id,
        table_id=record.table_id,
        session_id=record.session_id,
        action=record.action,
        target_track_id=record.target_track_id,
        execute_at=record.execute_at,
        state=SoundEventState(record.state),
    )


class PostgresTableRepository(TableRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, table: Table) -> None:
        await asyncio.to_thread(self._save_sync, table)

    def _save_sync(self, table: Table) -> None:
        with self._session_factory() as session:
            session: Session
            record = session.get(TableRecord, table.id)
            players_payload = _to_table_record_payload(table)
            if record is None:
                record = TableRecord(
                    id=table.id,
                    organization_id=table.organization_id,
                    name=table.name,
                    players=players_payload,
                )
                session.add(record)
            else:
                record.name = table.name
                record.players = players_payload
            session.commit()

    async def get_by_id(self, table_id: str) -> Table | None:
        return await asyncio.to_thread(self._get_by_id_sync, table_id)

    def _get_by_id_sync(self, table_id: str) -> Table | None:
        with self._session_factory() as session:
            session: Session
            record = session.get(TableRecord, table_id)
            if record is None:
                return None
            return _to_table_domain(record)


class PostgresSoundEventRepository(SoundEventRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, sound_event: SoundEvent) -> None:
        await asyncio.to_thread(self._save_sync, sound_event)

    def _save_sync(self, sound_event: SoundEvent) -> None:
        with self._session_factory() as session:
            session: Session
            record = session.get(SoundEventRecord, sound_event.id)
            if record is None:
                record = SoundEventRecord(
                    id=sound_event.id,
                    table_id=sound_event.table_id,
                    session_id=sound_event.session_id,
                    action=sound_event.action,
                    target_track_id=sound_event.target_track_id,
                    execute_at=sound_event.execute_at,
                    state=sound_event.state.value,
                )
                session.add(record)
            else:
                record.action = sound_event.action
                record.target_track_id = sound_event.target_track_id
                record.execute_at = sound_event.execute_at
                record.state = sound_event.state.value
            session.commit()

    async def list_due(self, up_to: datetime) -> list[SoundEvent]:
        return await asyncio.to_thread(self._list_due_sync, up_to.astimezone(UTC))

    def _list_due_sync(self, up_to: datetime) -> list[SoundEvent]:
        with self._session_factory() as session:
            session: Session
            stmt: Select[tuple[SoundEventRecord]] = select(SoundEventRecord).where(
                SoundEventRecord.execute_at <= up_to
            )
            rows = session.execute(stmt).scalars().all()
            return [_to_sound_event_domain(row) for row in rows]


class PostgresAuditLogRepository(AuditLogRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, entry: AuditLog) -> None:
        await asyncio.to_thread(self._save_sync, entry)

    def _save_sync(self, entry: AuditLog) -> None:
        with self._session_factory() as session:
            session: Session
            record = AuditLogRecord(
                id=entry.id,
                organization_id=entry.organization_id,
                actor_id=entry.actor_id,
                action=entry.action,
                target=entry.target,
                data=entry.data,
                created_at=entry.created_at,
            )
            session.add(record)
            session.commit()

    async def list_by_organization(self, organization_id: str) -> list[AuditLog]:
        return await asyncio.to_thread(self._list_by_organization_sync, organization_id)

    def _list_by_organization_sync(self, organization_id: str) -> list[AuditLog]:
        with self._session_factory() as session:
            session: Session
            stmt: Select[tuple[AuditLogRecord]] = (
                select(AuditLogRecord)
                .where(AuditLogRecord.organization_id == organization_id)
                .order_by(AuditLogRecord.created_at.desc())
            )
            rows = session.execute(stmt).scalars().all()
            return [
                AuditLog(
                    id=row.id,
                    organization_id=row.organization_id,
                    actor_id=row.actor_id,
                    action=row.action,
                    target=row.target,
                    data=row.data,
                    created_at=row.created_at,
                )
                for row in rows
            ]
