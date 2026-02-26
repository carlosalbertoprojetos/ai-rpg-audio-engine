from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError

from app.application.ports.security import TokenPayload, TokenService
from app.core.config import Settings


class JwtTokenService(TokenService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def encode(self, payload: TokenPayload) -> str:
        now = datetime.now(UTC)
        claims = {
            "sub": payload.sub,
            "email": payload.email,
            "organization_id": payload.organization_id,
            "roles": payload.roles,
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.jwt_exp_minutes),
        }
        return jwt.encode(
            claims,
            self._settings.jwt_secret,
            algorithm=self._settings.jwt_algorithm,
        )

    def decode(self, token: str) -> TokenPayload:
        try:
            claims = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
            )
        except InvalidTokenError as exc:
            raise ValueError("invalid token") from exc

        roles = claims.get("roles", [])
        if not isinstance(roles, list):
            raise ValueError("invalid token roles")
        return TokenPayload(
            sub=str(claims["sub"]),
            email=str(claims["email"]),
            organization_id=str(claims["organization_id"]),
            roles=[str(role) for role in roles],
        )

