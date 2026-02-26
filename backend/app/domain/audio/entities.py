from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4


class SoundEventState(str, Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass(slots=True)
class AudioTrack:
    id: str
    organization_id: str
    title: str
    s3_key: str
    duration_seconds: int

    @classmethod
    def create(
        cls, organization_id: str, title: str, s3_key: str, duration_seconds: int
    ) -> "AudioTrack":
        return cls(
            id=str(uuid4()),
            organization_id=organization_id,
            title=title,
            s3_key=s3_key,
            duration_seconds=duration_seconds,
        )


@dataclass(slots=True)
class Trigger:
    id: str
    table_id: str
    condition_type: str
    payload: dict[str, str]

    @classmethod
    def create(cls, table_id: str, condition_type: str, payload: dict[str, str]) -> "Trigger":
        return cls(
            id=str(uuid4()),
            table_id=table_id,
            condition_type=condition_type,
            payload=payload,
        )


@dataclass(slots=True)
class AIContext:
    id: str
    session_id: str
    mood: str
    recommended_track_tags: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, session_id: str, mood: str, recommended_track_tags: list[str]) -> "AIContext":
        return cls(
            id=str(uuid4()),
            session_id=session_id,
            mood=mood,
            recommended_track_tags=recommended_track_tags,
        )


@dataclass(slots=True)
class SoundEvent:
    id: str
    table_id: str
    session_id: str
    action: str
    target_track_id: str | None
    execute_at: datetime
    state: SoundEventState = SoundEventState.PENDING

    @classmethod
    def schedule(
        cls,
        table_id: str,
        session_id: str,
        action: str,
        execute_at: datetime,
        target_track_id: str | None = None,
    ) -> "SoundEvent":
        return cls(
            id=str(uuid4()),
            table_id=table_id,
            session_id=session_id,
            action=action,
            target_track_id=target_track_id,
            execute_at=execute_at,
        )

    def mark_executed(self) -> None:
        self.state = SoundEventState.EXECUTED
