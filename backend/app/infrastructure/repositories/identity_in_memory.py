from uuid import uuid4

from app.application.ports.identity import AuthProfile, IdentityRepository


class InMemoryIdentityRepository(IdentityRepository):
    def __init__(self) -> None:
        self._users: dict[tuple[str, str], AuthProfile] = {}

    async def find_auth_profile(self, email: str, organization_id: str) -> AuthProfile | None:
        return self._users.get((email, organization_id))

    async def register_user(
        self,
        email: str,
        display_name: str,
        password_hash: str,
        organization_id: str,
        role: str,
    ) -> AuthProfile:
        profile = AuthProfile(
            user_id=str(uuid4()),
            email=email,
            display_name=display_name,
            password_hash=password_hash,
            organization_id=organization_id,
            role=role,
        )
        self._users[(email, organization_id)] = profile
        return profile

