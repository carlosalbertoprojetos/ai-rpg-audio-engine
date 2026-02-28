from typing import Protocol

from app.domain.audio.entities import AIContext, AudioTrack, Trigger
from app.domain.identity.entities import Organization
from app.domain.tableops.entities import Session


class OrganizationRepository(Protocol):
    async def save(self, organization: Organization) -> None: ...

    async def get_by_id(self, organization_id: str) -> Organization | None: ...


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...

    async def get_by_id(self, session_id: str) -> Session | None: ...

    async def get_running_by_table(self, table_id: str) -> Session | None: ...


class AudioTrackRepository(Protocol):
    async def save(self, track: AudioTrack) -> None: ...

    async def list_by_organization(self, organization_id: str) -> list[AudioTrack]: ...


class TriggerRepository(Protocol):
    async def save(self, trigger: Trigger) -> None: ...

    async def list_by_table(self, table_id: str) -> list[Trigger]: ...


class AIContextRepository(Protocol):
    async def save(self, context: AIContext) -> None: ...

    async def list_by_session(self, session_id: str) -> list[AIContext]: ...

