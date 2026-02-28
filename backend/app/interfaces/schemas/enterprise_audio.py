from pydantic import BaseModel, Field


class CreateAudioTrackRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    s3_key: str = Field(min_length=1, max_length=255)
    duration_seconds: int = Field(gt=0, lt=72000)


class AudioTrackResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    s3_key: str
    duration_seconds: int


class CreateTriggerRequest(BaseModel):
    table_id: str = Field(min_length=1)
    condition_type: str = Field(min_length=1, max_length=80)
    payload: dict[str, str] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    id: str
    table_id: str
    condition_type: str
    payload: dict[str, str]


class GenerateAIContextRequest(BaseModel):
    session_id: str = Field(min_length=1)
    mood: str = Field(min_length=1, max_length=64)


class AIContextResponse(BaseModel):
    id: str
    session_id: str
    mood: str
    recommended_track_tags: list[str]

