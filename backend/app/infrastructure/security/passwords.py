from passlib.context import CryptContext

from app.application.ports.security import PasswordHasher


class Pbkdf2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    def hash(self, value: str) -> str:
        return self._context.hash(value)

    def verify(self, value: str, hashed_value: str) -> bool:
        return self._context.verify(value, hashed_value)
