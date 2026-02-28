from pydantic import BaseModel, EmailStr, Field


class UserSummaryResponse(BaseModel):
    user_id: str
    email: EmailStr
    display_name: str
    organization_id: str
    role: str


class UpdateUserRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, min_length=1, max_length=32)

