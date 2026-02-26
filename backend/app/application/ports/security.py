from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True, frozen=True)
class TokenPayload:
    sub: str
    email: str
    organization_id: str
    roles: list[str]


class PasswordHasher(Protocol):
    def hash(self, value: str) -> str: ...

    def verify(self, value: str, hashed_value: str) -> bool: ...


class TokenService(Protocol):
    def encode(self, payload: TokenPayload) -> str: ...

    def decode(self, token: str) -> TokenPayload: ...

