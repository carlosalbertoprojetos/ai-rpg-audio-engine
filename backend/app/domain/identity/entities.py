from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


@dataclass(slots=True)
class User:
    id: str
    email: str
    display_name: str
    status: UserStatus = UserStatus.ACTIVE

    @classmethod
    def create(cls, email: str, display_name: str) -> "User":
        return cls(id=str(uuid4()), email=email, display_name=display_name)


@dataclass(slots=True)
class Subscription:
    plan: str
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    billing_cycle: str = "monthly"


@dataclass(slots=True)
class Organization:
    id: str
    name: str
    owner_user_id: str
    subscription: Subscription

    @classmethod
    def create(cls, name: str, owner_user_id: str, plan: str = "starter") -> "Organization":
        return cls(
            id=str(uuid4()),
            name=name,
            owner_user_id=owner_user_id,
            subscription=Subscription(plan=plan),
        )

