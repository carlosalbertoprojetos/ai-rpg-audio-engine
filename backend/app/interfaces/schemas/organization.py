from pydantic import BaseModel, Field


class UpdatePlanRequest(BaseModel):
    plan: str = Field(min_length=1, max_length=32)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    owner_user_id: str
    subscription_plan: str
    subscription_status: str
    billing_cycle: str

