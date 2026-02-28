from dataclasses import dataclass

from app.application.governance.use_cases import RecordAuditEventCommand, RecordAuditEventUseCase
from app.application.ports.enterprise import OrganizationRepository
from app.domain.identity.entities import Organization


@dataclass(slots=True, frozen=True)
class EnsureOrganizationCommand:
    organization_id: str
    owner_user_id: str
    name: str
    plan: str = "starter"


@dataclass(slots=True, frozen=True)
class UpdateSubscriptionPlanCommand:
    organization_id: str
    actor_id: str
    plan: str


class EnsureOrganizationUseCase:
    def __init__(self, repository: OrganizationRepository) -> None:
        self._repository = repository

    async def __call__(self, command: EnsureOrganizationCommand) -> Organization:
        existing = await self._repository.get_by_id(command.organization_id)
        if existing is not None:
            return existing
        organization = Organization(
            id=command.organization_id,
            name=command.name,
            owner_user_id=command.owner_user_id,
            subscription=Organization.create(
                name=command.name,
                owner_user_id=command.owner_user_id,
                plan=command.plan,
            ).subscription,
        )
        await self._repository.save(organization)
        return organization


class UpdateSubscriptionPlanUseCase:
    def __init__(
        self,
        repository: OrganizationRepository,
        record_audit: RecordAuditEventUseCase,
    ) -> None:
        self._repository = repository
        self._record_audit = record_audit

    async def __call__(self, command: UpdateSubscriptionPlanCommand) -> Organization:
        organization = await self._repository.get_by_id(command.organization_id)
        if organization is None:
            raise ValueError("organization not found")
        organization.subscription.plan = command.plan
        await self._repository.save(organization)
        await self._record_audit(
            RecordAuditEventCommand(
                organization_id=organization.id,
                actor_id=command.actor_id,
                action="subscription.plan.updated",
                target=organization.id,
                data={"plan": command.plan},
            )
        )
        return organization

