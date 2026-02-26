from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=120)
    organization_id: str = Field(min_length=1, max_length=64)
    role: str = Field(default="narrator", min_length=1, max_length=32)


class IssueTokenRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=120)
    organization_id: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

