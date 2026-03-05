from datetime import UTC, datetime

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
from app.domain.audio.entities import AIContext, AudioTrack, SoundEvent, Trigger
from app.domain.governance.entities import AuditLog
from app.domain.identity.entities import Organization
from app.domain.tableops.entities import Session, SessionState, Table


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


class InMemoryOrganizationRepository(OrganizationRepository):
    def __init__(self) -> None:
        self._items: dict[str, Organization] = {}

    async def save(self, organization: Organization) -> None:
        self._items[organization.id] = organization

    async def get_by_id(self, organization_id: str) -> Organization | None:
        return self._items.get(organization_id)


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._items: dict[str, Session] = {}

    async def save(self, session: Session) -> None:
        self._items[session.id] = session

    async def get_by_id(self, session_id: str) -> Session | None:
        return self._items.get(session_id)

    async def get_running_by_table(self, table_id: str) -> Session | None:
        for session in self._items.values():
            if session.table_id == table_id and session.state == SessionState.RUNNING:
                return session
        return None


class InMemoryAudioTrackRepository(AudioTrackRepository):
    def __init__(self) -> None:
        self._items: dict[str, AudioTrack] = {}

    async def save(self, track: AudioTrack) -> None:
        self._items[track.id] = track

    async def list_by_organization(self, organization_id: str) -> list[AudioTrack]:
        return [item for item in self._items.values() if item.organization_id == organization_id]

    async def get_by_id(self, track_id: str) -> AudioTrack | None:
        return self._items.get(track_id)


class InMemoryTriggerRepository(TriggerRepository):
    def __init__(self) -> None:
        self._items: dict[str, Trigger] = {}

    async def save(self, trigger: Trigger) -> None:
        self._items[trigger.id] = trigger

    async def list_by_table(self, table_id: str) -> list[Trigger]:
        return [item for item in self._items.values() if item.table_id == table_id]


class InMemoryAIContextRepository(AIContextRepository):
    def __init__(self) -> None:
        self._items: dict[str, AIContext] = {}

    async def save(self, context: AIContext) -> None:
        self._items[context.id] = context

    async def list_by_session(self, session_id: str) -> list[AIContext]:
        return [item for item in self._items.values() if item.session_id == session_id]
