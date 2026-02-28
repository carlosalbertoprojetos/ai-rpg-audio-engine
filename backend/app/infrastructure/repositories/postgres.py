import asyncio
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

from app.application.ports.enterprise import (
    AIContextRepository,
    AudioTrackRepository,
    OrganizationRepository,
    SessionRepository,
    TriggerRepository,
)
from app.application.ports.repositories import (
    AuditLogRepository,
    SoundEventRepository,
    TableRepository,
)
from app.domain.audio.entities import AIContext, AudioTrack, SoundEvent, SoundEventState, Trigger
from app.domain.governance.entities import AuditLog
from app.domain.identity.entities import Organization, Subscription, SubscriptionStatus
from app.domain.tableops.entities import Player, PlayerAvailability, Session, SessionState, Table
from app.infrastructure.db.models import (
    AIContextRecord,
    AudioTrackRecord,
    AuditLogRecord,
    OrganizationRecord,
    SessionRecord,
    SoundEventRecord,
    TableRecord,
    TriggerRecord,
)


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
            session: OrmSession
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
            session: OrmSession
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
            session: OrmSession
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
            session: OrmSession
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
            session: OrmSession
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
            session: OrmSession
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


class PostgresOrganizationRepository(OrganizationRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, organization: Organization) -> None:
        await asyncio.to_thread(self._save_sync, organization)

    def _save_sync(self, organization: Organization) -> None:
        with self._session_factory() as session:
            session: OrmSession
            record = session.get(OrganizationRecord, organization.id)
            if record is None:
                record = OrganizationRecord(
                    id=organization.id,
                    name=organization.name,
                    owner_user_id=organization.owner_user_id,
                    subscription_plan=organization.subscription.plan,
                    subscription_status=organization.subscription.status.value,
                    billing_cycle=organization.subscription.billing_cycle,
                )
                session.add(record)
            else:
                record.name = organization.name
                record.subscription_plan = organization.subscription.plan
                record.subscription_status = organization.subscription.status.value
                record.billing_cycle = organization.subscription.billing_cycle
            session.commit()

    async def get_by_id(self, organization_id: str) -> Organization | None:
        return await asyncio.to_thread(self._get_by_id_sync, organization_id)

    def _get_by_id_sync(self, organization_id: str) -> Organization | None:
        with self._session_factory() as session:
            session: OrmSession
            record = session.get(OrganizationRecord, organization_id)
            if record is None:
                return None
            return Organization(
                id=record.id,
                name=record.name,
                owner_user_id=record.owner_user_id,
                subscription=Subscription(
                    plan=record.subscription_plan,
                    status=SubscriptionStatus(record.subscription_status),
                    billing_cycle=record.billing_cycle,
                ),
            )


class PostgresSessionRepository(SessionRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, session_entity: Session) -> None:
        await asyncio.to_thread(self._save_sync, session_entity)

    def _save_sync(self, session_entity: Session) -> None:
        with self._session_factory() as session:
            session: OrmSession
            record = session.get(SessionRecord, session_entity.id)
            if record is None:
                record = SessionRecord(
                    id=session_entity.id,
                    table_id=session_entity.table_id,
                    state=session_entity.state.value,
                    started_at=session_entity.started_at,
                    ended_at=session_entity.ended_at,
                )
                session.add(record)
            else:
                record.state = session_entity.state.value
                record.ended_at = session_entity.ended_at
            session.commit()

    async def get_by_id(self, session_id: str) -> Session | None:
        return await asyncio.to_thread(self._get_by_id_sync, session_id)

    def _get_by_id_sync(self, session_id: str) -> Session | None:
        with self._session_factory() as session:
            session: OrmSession
            record = session.get(SessionRecord, session_id)
            if record is None:
                return None
            return Session(
                id=record.id,
                table_id=record.table_id,
                state=SessionState(record.state),
                started_at=record.started_at,
                ended_at=record.ended_at,
            )

    async def get_running_by_table(self, table_id: str) -> Session | None:
        return await asyncio.to_thread(self._get_running_by_table_sync, table_id)

    def _get_running_by_table_sync(self, table_id: str) -> Session | None:
        with self._session_factory() as session:
            session: OrmSession
            stmt: Select[tuple[SessionRecord]] = (
                select(SessionRecord)
                .where(SessionRecord.table_id == table_id)
                .where(SessionRecord.state == SessionState.RUNNING.value)
                .order_by(SessionRecord.started_at.desc())
            )
            row = session.execute(stmt).scalars().first()
            if row is None:
                return None
            return Session(
                id=row.id,
                table_id=row.table_id,
                state=SessionState(row.state),
                started_at=row.started_at,
                ended_at=row.ended_at,
            )


class PostgresAudioTrackRepository(AudioTrackRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, track: AudioTrack) -> None:
        await asyncio.to_thread(self._save_sync, track)

    def _save_sync(self, track: AudioTrack) -> None:
        with self._session_factory() as session:
            session: OrmSession
            record = session.get(AudioTrackRecord, track.id)
            if record is None:
                record = AudioTrackRecord(
                    id=track.id,
                    organization_id=track.organization_id,
                    title=track.title,
                    s3_key=track.s3_key,
                    duration_seconds=track.duration_seconds,
                )
                session.add(record)
            else:
                record.title = track.title
                record.s3_key = track.s3_key
                record.duration_seconds = track.duration_seconds
            session.commit()

    async def list_by_organization(self, organization_id: str) -> list[AudioTrack]:
        return await asyncio.to_thread(self._list_by_organization_sync, organization_id)

    def _list_by_organization_sync(self, organization_id: str) -> list[AudioTrack]:
        with self._session_factory() as session:
            session: OrmSession
            stmt: Select[tuple[AudioTrackRecord]] = (
                select(AudioTrackRecord).where(AudioTrackRecord.organization_id == organization_id)
            )
            rows = session.execute(stmt).scalars().all()
            return [
                AudioTrack(
                    id=row.id,
                    organization_id=row.organization_id,
                    title=row.title,
                    s3_key=row.s3_key,
                    duration_seconds=row.duration_seconds,
                )
                for row in rows
            ]


class PostgresTriggerRepository(TriggerRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, trigger: Trigger) -> None:
        await asyncio.to_thread(self._save_sync, trigger)

    def _save_sync(self, trigger: Trigger) -> None:
        with self._session_factory() as session:
            session: OrmSession
            record = TriggerRecord(
                id=trigger.id,
                table_id=trigger.table_id,
                condition_type=trigger.condition_type,
                payload=trigger.payload,
            )
            session.add(record)
            session.commit()

    async def list_by_table(self, table_id: str) -> list[Trigger]:
        return await asyncio.to_thread(self._list_by_table_sync, table_id)

    def _list_by_table_sync(self, table_id: str) -> list[Trigger]:
        with self._session_factory() as session:
            session: Session
            stmt: Select[tuple[TriggerRecord]] = select(TriggerRecord).where(
                TriggerRecord.table_id == table_id
            )
            rows = session.execute(stmt).scalars().all()
            return [
                Trigger(
                    id=row.id,
                    table_id=row.table_id,
                    condition_type=row.condition_type,
                    payload=row.payload,
                )
                for row in rows
            ]


class PostgresAIContextRepository(AIContextRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def save(self, context: AIContext) -> None:
        await asyncio.to_thread(self._save_sync, context)

    def _save_sync(self, context: AIContext) -> None:
        with self._session_factory() as session:
            session: Session
            row = AIContextRecord(
                id=context.id,
                session_id=context.session_id,
                mood=context.mood,
                recommended_track_tags=context.recommended_track_tags,
                created_at=context.created_at,
            )
            session.add(row)
            session.commit()

    async def list_by_session(self, session_id: str) -> list[AIContext]:
        return await asyncio.to_thread(self._list_by_session_sync, session_id)

    def _list_by_session_sync(self, session_id: str) -> list[AIContext]:
        with self._session_factory() as session:
            session: Session
            stmt: Select[tuple[AIContextRecord]] = select(AIContextRecord).where(
                AIContextRecord.session_id == session_id
            )
            rows = session.execute(stmt).scalars().all()
            return [
                AIContext(
                    id=row.id,
                    session_id=row.session_id,
                    mood=row.mood,
                    recommended_track_tags=row.recommended_track_tags,
                    created_at=row.created_at,
                )
                for row in rows
            ]
