from datetime import datetime

from pydantic import BaseModel, Field


class ScheduleSoundEventRequest(BaseModel):
    table_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    execute_at: datetime
    target_track_id: str | None = None


class SoundEventResponse(BaseModel):
    id: str
    table_id: str
    session_id: str
    action: str
    execute_at: datetime
    state: str
    target_track_id: str | None = None
