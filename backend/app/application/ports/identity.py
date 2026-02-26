from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class AuthProfile:
    user_id: str
    email: str
    display_name: str
    password_hash: str
    organization_id: str
    role: str


@dataclass(slots=True, frozen=True)
class UserSummary:
    user_id: str
    email: str
    display_name: str
    organization_id: str
    role: str


class IdentityRepository(Protocol):
    async def find_auth_profile(self, email: str, organization_id: str) -> AuthProfile | None: ...

    async def register_user(
        self,
        email: str,
        display_name: str,
        password_hash: str,
        organization_id: str,
        role: str,
    ) -> AuthProfile: ...

    async def list_users(self, organization_id: str) -> list[UserSummary]: ...

    async def update_user(
        self,
        organization_id: str,
        user_id: str,
        display_name: str | None,
        role: str | None,
    ) -> UserSummary: ...
