import asyncio
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.identity import AuthProfile, IdentityRepository
from app.infrastructure.db.models import MembershipRecord, UserRecord


class PostgresIdentityRepository(IdentityRepository):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    async def find_auth_profile(self, email: str, organization_id: str) -> AuthProfile | None:
        return await asyncio.to_thread(self._find_auth_profile_sync, email, organization_id)

    def _find_auth_profile_sync(self, email: str, organization_id: str) -> AuthProfile | None:
        with self._session_factory() as session:
            session: Session
            stmt: Select[tuple[UserRecord, MembershipRecord]] = (
                select(UserRecord, MembershipRecord)
                .join(MembershipRecord, MembershipRecord.user_id == UserRecord.id)
                .where(UserRecord.email == email)
                .where(MembershipRecord.organization_id == organization_id)
            )
            row = session.execute(stmt).first()
            if row is None:
                return None
            user, membership = row
            return AuthProfile(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                password_hash=user.password_hash,
                organization_id=membership.organization_id,
                role=membership.role,
            )

    async def register_user(
        self,
        email: str,
        display_name: str,
        password_hash: str,
        organization_id: str,
        role: str,
    ) -> AuthProfile:
        return await asyncio.to_thread(
            self._register_user_sync,
            email,
            display_name,
            password_hash,
            organization_id,
            role,
        )

    def _register_user_sync(
        self,
        email: str,
        display_name: str,
        password_hash: str,
        organization_id: str,
        role: str,
    ) -> AuthProfile:
        with self._session_factory() as session:
            session: Session

            user_stmt: Select[tuple[UserRecord]] = select(UserRecord).where(
                UserRecord.email == email
            )
            user = session.execute(user_stmt).scalar_one_or_none()
            if user is None:
                user = UserRecord(
                    id=str(uuid4()),
                    email=email,
                    display_name=display_name,
                    password_hash=password_hash,
                    status="active",
                )
                session.add(user)
                session.flush()
            else:
                user.display_name = display_name
                user.password_hash = password_hash

            membership_stmt: Select[tuple[MembershipRecord]] = (
                select(MembershipRecord)
                .where(MembershipRecord.user_id == user.id)
                .where(MembershipRecord.organization_id == organization_id)
            )
            membership = session.execute(membership_stmt).scalar_one_or_none()
            if membership is None:
                membership = MembershipRecord(
                    id=str(uuid4()),
                    user_id=user.id,
                    organization_id=organization_id,
                    role=role,
                )
                session.add(membership)
            else:
                membership.role = role

            session.commit()
            return AuthProfile(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                password_hash=user.password_hash,
                organization_id=membership.organization_id,
                role=membership.role,
            )
