from uuid import uuid4

from app.application.ports.identity import AuthProfile, IdentityRepository, UserSummary


class InMemoryIdentityRepository(IdentityRepository):
    def __init__(self) -> None:
        self._users: dict[tuple[str, str], AuthProfile] = {}
        self._users_by_id: dict[str, AuthProfile] = {}

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
        self._users_by_id[profile.user_id] = profile
        return profile

    async def list_users(self, organization_id: str) -> list[UserSummary]:
        return [
            UserSummary(
                user_id=profile.user_id,
                email=profile.email,
                display_name=profile.display_name,
                organization_id=profile.organization_id,
                role=profile.role,
            )
            for profile in self._users_by_id.values()
            if profile.organization_id == organization_id
        ]

    async def update_user(
        self,
        organization_id: str,
        user_id: str,
        display_name: str | None,
        role: str | None,
    ) -> UserSummary:
        profile = self._users_by_id.get(user_id)
        if profile is None:
            raise ValueError("user not found")
        if profile.organization_id != organization_id:
            raise ValueError("organization scope mismatch")

        updated = AuthProfile(
            user_id=profile.user_id,
            email=profile.email,
            display_name=(
                display_name.strip() if display_name is not None else profile.display_name
            ),
            password_hash=profile.password_hash,
            organization_id=profile.organization_id,
            role=(role.strip() if role is not None else profile.role),
        )
        self._users_by_id[user_id] = updated
        self._users[(updated.email, updated.organization_id)] = updated

        return UserSummary(
            user_id=updated.user_id,
            email=updated.email,
            display_name=updated.display_name,
            organization_id=updated.organization_id,
            role=updated.role,
        )
