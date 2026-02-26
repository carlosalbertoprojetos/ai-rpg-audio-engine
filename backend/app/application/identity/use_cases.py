from dataclasses import dataclass

from app.application.ports.identity import AuthProfile, IdentityRepository, UserSummary
from app.application.ports.security import PasswordHasher, TokenPayload, TokenService


@dataclass(slots=True, frozen=True)
class RegisterUserCommand:
    email: str
    display_name: str
    password: str
    organization_id: str
    role: str


@dataclass(slots=True, frozen=True)
class IssueTokenCommand:
    email: str
    password: str
    organization_id: str


@dataclass(slots=True, frozen=True)
class AuthTokenResult:
    access_token: str
    token_type: str = "bearer"


class RegisterUserUseCase:
    def __init__(self, repository: IdentityRepository, hasher: PasswordHasher) -> None:
        self._repository = repository
        self._hasher = hasher

    async def __call__(self, command: RegisterUserCommand) -> AuthProfile:
        password_hash = self._hasher.hash(command.password)
        return await self._repository.register_user(
            email=command.email.strip().lower(),
            display_name=command.display_name.strip(),
            password_hash=password_hash,
            organization_id=command.organization_id,
            role=command.role,
        )


class IssueTokenUseCase:
    def __init__(
        self,
        repository: IdentityRepository,
        hasher: PasswordHasher,
        token_service: TokenService,
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._token_service = token_service

    async def __call__(self, command: IssueTokenCommand) -> AuthTokenResult:
        profile = await self._repository.find_auth_profile(
            email=command.email.strip().lower(),
            organization_id=command.organization_id,
        )
        if profile is None:
            raise ValueError("invalid credentials")
        if not self._hasher.verify(command.password, profile.password_hash):
            raise ValueError("invalid credentials")
        payload = TokenPayload(
            sub=profile.user_id,
            email=profile.email,
            organization_id=profile.organization_id,
            roles=[profile.role],
        )
        return AuthTokenResult(access_token=self._token_service.encode(payload))


@dataclass(slots=True, frozen=True)
class ListUsersCommand:
    organization_id: str


class ListUsersUseCase:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def __call__(self, command: ListUsersCommand) -> list[UserSummary]:
        return await self._repository.list_users(command.organization_id)


@dataclass(slots=True, frozen=True)
class UpdateUserCommand:
    organization_id: str
    user_id: str
    display_name: str | None = None
    role: str | None = None


class UpdateUserUseCase:
    def __init__(self, repository: IdentityRepository) -> None:
        self._repository = repository

    async def __call__(self, command: UpdateUserCommand) -> UserSummary:
        return await self._repository.update_user(
            organization_id=command.organization_id,
            user_id=command.user_id,
            display_name=command.display_name,
            role=command.role,
        )
