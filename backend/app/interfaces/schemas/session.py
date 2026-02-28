from datetime import datetime

from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    table_id: str = Field(min_length=1)


class SessionResponse(BaseModel):
    id: str
    table_id: str
    state: str
    started_at: datetime
    ended_at: datetime | None = None

