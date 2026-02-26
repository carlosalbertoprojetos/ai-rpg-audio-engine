from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4


class PlayerAvailability(str, Enum):
    AVAILABLE = "green"
    UNAVAILABLE = "red"


class SessionState(str, Enum):
    RUNNING = "running"
    FINISHED = "finished"


@dataclass(slots=True)
class Player:
    id: str
    display_name: str
    availability: PlayerAvailability = PlayerAvailability.AVAILABLE
    user_id: str | None = None

    @classmethod
    def create(cls, display_name: str, user_id: str | None = None) -> "Player":
        return cls(id=str(uuid4()), display_name=display_name, user_id=user_id)

    def set_availability(self, availability: PlayerAvailability) -> None:
        self.availability = availability


@dataclass(slots=True)
class Table:
    id: str
    organization_id: str
    name: str
    players: dict[str, Player] = field(default_factory=dict)

    @classmethod
    def create(cls, organization_id: str, name: str) -> "Table":
        return cls(id=str(uuid4()), organization_id=organization_id, name=name)

    def add_player(self, player: Player) -> None:
        if player.id in self.players:
            raise ValueError("player already exists in table")
        self.players[player.id] = player

    def update_player_availability(
        self, player_id: str, availability: PlayerAvailability
    ) -> Player:
        player = self.players.get(player_id)
        if player is None:
            raise ValueError("player not found")
        player.set_availability(availability)
        return player


@dataclass(slots=True)
class Session:
    id: str
    table_id: str
    state: SessionState = SessionState.RUNNING
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None

    @classmethod
    def start(cls, table_id: str) -> "Session":
        return cls(id=str(uuid4()), table_id=table_id)

    def finish(self) -> None:
        self.state = SessionState.FINISHED
        self.ended_at = datetime.now(UTC)

