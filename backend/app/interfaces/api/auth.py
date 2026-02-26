from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.ports.security import TokenPayload
from app.container import Container

bearer_scheme = HTTPBearer(auto_error=True)


@dataclass(slots=True, frozen=True)
class AuthContext:
    user_id: str
    email: str
    organization_id: str
    roles: list[str]


def _build_context(payload: TokenPayload) -> AuthContext:
    return AuthContext(
        user_id=payload.sub,
        email=payload.email,
        organization_id=payload.organization_id,
        roles=payload.roles,
    )


def build_auth_dependency(get_container: Callable[[], Container]):
    def get_auth_context(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> AuthContext:
        container: Container = get_container()
        try:
            payload = container.token_service.decode(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token",
            ) from exc
        return _build_context(payload)

    return get_auth_context


def require_roles(
    auth_context: AuthContext,
    allowed_roles: set[str],
    action_name: str,
) -> None:
    if not allowed_roles.intersection(set(auth_context.roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"role not allowed for {action_name}",
        )


def ensure_same_organization(auth_context: AuthContext, organization_id: str) -> None:
    if auth_context.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="organization scope mismatch",
        )
