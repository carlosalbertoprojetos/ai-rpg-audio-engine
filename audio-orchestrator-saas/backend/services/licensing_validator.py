"""License compatibility checks for SaaS-safe asset distribution."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LicensingPolicy:
    """Allowed and denied license classes."""

    allowed: set[str]
    denied: set[str]


DEFAULT_POLICY = LicensingPolicy(
    allowed={
        "royalty_free",
        "commercial_safe",
        "cc0",
        "cc_by",
        "standard_commercial",
    },
    denied={
        "cc_by_nc",
        "cc_by_nc_sa",
        "editorial_only",
        "personal_use_only",
        "unknown",
    },
)


class LicensingValidator:
    """Ensures provider assets comply with SaaS distribution policies."""

    def __init__(self, policy: LicensingPolicy = DEFAULT_POLICY) -> None:
        self._policy = policy

    def validate(self, license_type: str) -> bool:
        canonical = license_type.strip().lower()
        if canonical in self._policy.denied:
            return False
        return canonical in self._policy.allowed
