from pydantic import BaseModel, Field

from app.domain.tableops.entities import PlayerAvailability


class CreateTableRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CreateTableResponse(BaseModel):
    id: str
    organization_id: str
    name: str


class AddPlayerRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    user_id: str | None = None


class PlayerResponse(BaseModel):
    id: str
    display_name: str
    availability: PlayerAvailability
    user_id: str | None = None


class UpdateAvailabilityRequest(BaseModel):
    availability: PlayerAvailability
