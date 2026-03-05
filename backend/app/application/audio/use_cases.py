from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.governance.use_cases import RecordAuditEventCommand, RecordAuditEventUseCase
from app.application.ports.enterprise import (
    AIContextRepository,
    AudioTrackRepository,
    TriggerRepository,
)
from app.application.ports.event_bus import EventBus
from app.application.ports.repositories import SoundEventRepository
from app.domain.audio.entities import AIContext, AudioTrack, SoundEvent, Trigger
from app.domain.shared.events import DomainEvent


@dataclass(slots=True, frozen=True)
class ScheduleSoundEventCommand:
    organization_id: str
    table_id: str
    session_id: str
    action: str
    execute_at: datetime
    target_track_id: str | None = None
    actor_id: str | None = None


@dataclass(slots=True, frozen=True)
class ExecuteDueSoundEventsCommand:
    up_to: datetime


class ScheduleSoundEventUseCase:
    def __init__(
        self,
        sound_event_repository: SoundEventRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._sound_event_repository = sound_event_repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: ScheduleSoundEventCommand) -> SoundEvent:
        execute_at = command.execute_at.astimezone(UTC)
        sound_event = SoundEvent.schedule(
            table_id=command.table_id,
            session_id=command.session_id,
            action=command.action,
            target_track_id=command.target_track_id,
            execute_at=execute_at,
        )
        await self._sound_event_repository.save(sound_event)

        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                action="sound.event.scheduled",
                target=sound_event.id,
                actor_id=command.actor_id,
                data={
                    "table_id": sound_event.table_id,
                    "session_id": sound_event.session_id,
                    "action": sound_event.action,
                },
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="sound.event.scheduled",
                payload={
                    "table_id": sound_event.table_id,
                    "session_id": sound_event.session_id,
                    "sound_event_id": sound_event.id,
                    "action": sound_event.action,
                    "execute_at": sound_event.execute_at.isoformat(),
                },
            )
        )
        return sound_event


class ExecuteDueSoundEventsUseCase:
    def __init__(self, sound_event_repository: SoundEventRepository, event_bus: EventBus) -> None:
        self._sound_event_repository = sound_event_repository
        self._event_bus = event_bus

    async def __call__(self, command: ExecuteDueSoundEventsCommand) -> list[SoundEvent]:
        due_events = await self._sound_event_repository.list_due(command.up_to)
        for sound_event in due_events:
            if sound_event.state.value != "pending":
                continue
            sound_event.mark_executed()
            await self._sound_event_repository.save(sound_event)
            await self._event_bus.publish(
                DomainEvent(
                    event_type="sound.event.executed",
                    payload={
                        "table_id": sound_event.table_id,
                        "session_id": sound_event.session_id,
                        "sound_event_id": sound_event.id,
                        "action": sound_event.action,
                        "target_track_id": sound_event.target_track_id or "",
                    },
                )
            )
        return due_events


@dataclass(slots=True, frozen=True)
class CreateAudioTrackCommand:
    organization_id: str
    title: str
    s3_key: str
    duration_seconds: int
    actor_id: str


class CreateAudioTrackUseCase:
    def __init__(
        self,
        repository: AudioTrackRepository,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._repository = repository
        self._record_audit = record_audit

    async def __call__(self, command: CreateAudioTrackCommand) -> AudioTrack:
        track = AudioTrack.create(
            organization_id=command.organization_id,
            title=command.title,
            s3_key=command.s3_key,
            duration_seconds=command.duration_seconds,
        )
        await self._repository.save(track)
        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action="audio.track.created",
                target=track.id,
                data={"title": track.title, "s3_key": track.s3_key},
            )
        )
        return track


@dataclass(slots=True, frozen=True)
class CreateTriggerCommand:
    organization_id: str
    table_id: str
    condition_type: str
    payload: dict[str, str]
    actor_id: str


class CreateTriggerUseCase:
    def __init__(
        self,
        repository: TriggerRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: CreateTriggerCommand) -> Trigger:
        trigger = Trigger.create(
            table_id=command.table_id,
            condition_type=command.condition_type,
            payload=command.payload,
        )
        await self._repository.save(trigger)
        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action="trigger.created",
                target=trigger.id,
                data={"table_id": trigger.table_id, "condition_type": trigger.condition_type},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="trigger.created",
                payload={"table_id": trigger.table_id, "trigger_id": trigger.id},
            )
        )
        return trigger


@dataclass(slots=True, frozen=True)
class GenerateAdaptiveAmbienceCommand:
    organization_id: str
    session_id: str
    mood: str
    actor_id: str


class GenerateAdaptiveAmbienceUseCase:
    def __init__(
        self,
        repository: AIContextRepository,
        event_bus: EventBus,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
        self._record_audit = record_audit

    async def __call__(self, command: GenerateAdaptiveAmbienceCommand) -> AIContext:
        tags = {
            "battle": ["combat", "drums", "tension"],
            "mystery": ["ambient", "dark", "echo"],
            "calm": ["nature", "wind", "soft"],
        }.get(command.mood, ["ambient"])
        context = AIContext.create(
            session_id=command.session_id,
            mood=command.mood,
            recommended_track_tags=tags,
        )
        await self._repository.save(context)
        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=command.organization_id,
                actor_id=command.actor_id,
                action="ai.ambience.generated",
                target=context.id,
                data={"session_id": context.session_id, "mood": context.mood},
            )
        )
        await self._event_bus.publish(
            DomainEvent(
                event_type="ai.ambience.generated",
                payload={
                    "session_id": context.session_id,
                    "mood": context.mood,
                    "tags": ",".join(context.recommended_track_tags),
                },
            )
        )
        return context
