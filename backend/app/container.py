from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.orm import sessionmaker

from app.application.audio.use_cases import ExecuteDueSoundEventsUseCase, ScheduleSoundEventUseCase
from app.application.governance.use_cases import RecordAuditEventUseCase
from app.application.identity.use_cases import IssueTokenUseCase, RegisterUserUseCase
from app.application.ports.identity import IdentityRepository
from app.application.ports.repositories import (
    AuditLogRepository,
    SoundEventRepository,
    TableRepository,
)
from app.application.ports.security import PasswordHasher, TokenService
from app.application.tableops.use_cases import (
    AddPlayerUseCase,
    CreateTableUseCase,
    UpdatePlayerAvailabilityUseCase,
)
from app.core.config import Settings
from app.infrastructure.db.session import bootstrap_schema, build_engine, build_session_factory
from app.infrastructure.messaging.in_memory_bus import InMemoryEventBus
from app.infrastructure.messaging.redis_bus import RedisEventBus
from app.infrastructure.repositories.identity_in_memory import InMemoryIdentityRepository
from app.infrastructure.repositories.identity_postgres import PostgresIdentityRepository
from app.infrastructure.repositories.in_memory import (
    InMemoryAuditLogRepository,
    InMemorySoundEventRepository,
    InMemoryTableRepository,
)
from app.infrastructure.repositories.postgres import (
    PostgresAuditLogRepository,
    PostgresSoundEventRepository,
    PostgresTableRepository,
)
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.tokens import JwtTokenService
from app.interfaces.ws.manager import TableSocketManager


@dataclass(slots=True)
class UseCases:
    create_table: CreateTableUseCase
    add_player: AddPlayerUseCase
    update_player_availability: UpdatePlayerAvailabilityUseCase
    schedule_sound_event: ScheduleSoundEventUseCase
    execute_due_sound_events: ExecuteDueSoundEventsUseCase
    record_audit_event: RecordAuditEventUseCase
    register_user: RegisterUserUseCase
    issue_token: IssueTokenUseCase


@dataclass(slots=True)
class Container:
    table_repository: TableRepository
    sound_event_repository: SoundEventRepository
    audit_repository: AuditLogRepository
    identity_repository: IdentityRepository
    event_bus: Any
    socket_manager: TableSocketManager
    token_service: TokenService
    password_hasher: PasswordHasher
    use_cases: UseCases
    session_factory: sessionmaker | None = None

    async def start(self) -> None:
        maybe_start = getattr(self.event_bus, "start", None)
        if callable(maybe_start):
            await maybe_start()

    async def stop(self) -> None:
        maybe_stop = getattr(self.event_bus, "stop", None)
        if callable(maybe_stop):
            await maybe_stop()


def build_container(settings: Settings) -> Container:
    table_repository: TableRepository
    sound_event_repository: SoundEventRepository
    audit_repository: AuditLogRepository
    identity_repository: IdentityRepository
    session_factory: sessionmaker | None = None

    if settings.repository_mode == "postgres":
        engine = build_engine(settings)
        bootstrap_schema(engine)
        session_factory = build_session_factory(engine)
        table_repository = PostgresTableRepository(session_factory)
        sound_event_repository = PostgresSoundEventRepository(session_factory)
        audit_repository = PostgresAuditLogRepository(session_factory)
        identity_repository = PostgresIdentityRepository(session_factory)
    else:
        table_repository = InMemoryTableRepository()
        sound_event_repository = InMemorySoundEventRepository()
        audit_repository = InMemoryAuditLogRepository()
        identity_repository = InMemoryIdentityRepository()

    if settings.event_bus_mode == "redis":
        redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
        event_bus: Any = RedisEventBus(redis_client)
    else:
        event_bus = InMemoryEventBus()

    socket_manager = TableSocketManager()
    token_service = JwtTokenService(settings)
    password_hasher = Pbkdf2PasswordHasher()

    record_audit_event = RecordAuditEventUseCase(audit_repository=audit_repository)
    create_table = CreateTableUseCase(table_repository, event_bus, record_audit_event)
    add_player = AddPlayerUseCase(table_repository, event_bus, record_audit_event)
    update_player_availability = UpdatePlayerAvailabilityUseCase(
        table_repository, event_bus, record_audit_event
    )
    schedule_sound_event = ScheduleSoundEventUseCase(
        sound_event_repository, event_bus, record_audit_event
    )
    execute_due_sound_events = ExecuteDueSoundEventsUseCase(sound_event_repository, event_bus)
    register_user = RegisterUserUseCase(identity_repository, password_hasher)
    issue_token = IssueTokenUseCase(identity_repository, password_hasher, token_service)

    event_bus.subscribe("*", socket_manager.broadcast_event)

    return Container(
        table_repository=table_repository,
        sound_event_repository=sound_event_repository,
        audit_repository=audit_repository,
        identity_repository=identity_repository,
        event_bus=event_bus,
        socket_manager=socket_manager,
        token_service=token_service,
        password_hasher=password_hasher,
        use_cases=UseCases(
            create_table=create_table,
            add_player=add_player,
            update_player_availability=update_player_availability,
            schedule_sound_event=schedule_sound_event,
            execute_due_sound_events=execute_due_sound_events,
            record_audit_event=record_audit_event,
            register_user=register_user,
            issue_token=issue_token,
        ),
        session_factory=session_factory,
    )
