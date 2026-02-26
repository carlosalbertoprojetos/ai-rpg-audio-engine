import pytest

from app.application.identity.use_cases import (
    IssueTokenCommand,
    IssueTokenUseCase,
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.core.config import Settings
from app.infrastructure.repositories.identity_in_memory import InMemoryIdentityRepository
from app.infrastructure.security.passwords import Pbkdf2PasswordHasher
from app.infrastructure.security.tokens import JwtTokenService


@pytest.mark.asyncio
async def test_register_and_issue_token() -> None:
    repository = InMemoryIdentityRepository()
    hasher = Pbkdf2PasswordHasher()
    token_service = JwtTokenService(Settings(jwt_secret="unit-test-secret-with-at-least-32-bytes"))

    register = RegisterUserUseCase(repository, hasher)
    issue = IssueTokenUseCase(repository, hasher, token_service)

    profile = await register(
        RegisterUserCommand(
            email="gm@unit.com",
            display_name="GM",
            password="StrongPass123",
            organization_id="org-unit",
            role="admin",
        )
    )
    assert profile.organization_id == "org-unit"

    token = await issue(
        IssueTokenCommand(
            email="gm@unit.com",
            password="StrongPass123",
            organization_id="org-unit",
        )
    )
    assert token.access_token
