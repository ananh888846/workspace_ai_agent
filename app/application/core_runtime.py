from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence


class CoreAuthorizationError(PermissionError):
    """Raised when a protected capability is not authorized."""


class AccountSelectionRequiredError(RuntimeError):
    """Raised when multiple accounts match and no account is selected."""


@dataclass(frozen=True)
class AgentContext:
    request_id: str
    organization_id: str
    user_id: str
    session_id: str | None = None
    device_id: str | None = None
    capability: str | None = None
    action: str | None = None
    target_account: str | None = None
    target_resource: str | None = None
    target_package: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExternalAccount:
    id: str
    user_id: str
    provider: str
    account_type: str
    external_account_id: str
    display_name: str | None = None
    email: str | None = None
    status: str = "active"


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    code: str


class AccountRepository(Protocol):
    def find_candidates(
        self,
        *,
        user_id: str,
        organization_id: str,
        provider: str,
        account_hint: str | None = None,
    ) -> Sequence[ExternalAccount]:
        ...


class PermissionRepository(Protocol):
    def has_capability_permission(
        self, *, user_id: str, capability: str
    ) -> bool:
        ...

    def has_account_access(
        self,
        *,
        organization_id: str,
        user_id: str,
        account: ExternalAccount,
        capability: str,
    ) -> bool:
        ...

    def has_resource_access(
        self,
        *,
        organization_id: str,
        user_id: str,
        resource_id: str,
        action: str,
    ) -> bool:
        ...


class CredentialRepository(Protocol):
    def resolve_authorized_credential(self, *, account: ExternalAccount) -> Any:
        ...


class AccountResolver:
    """Resolve account metadata without touching credentials."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        user_id: str,
        organization_id: str,
        provider: str,
        account_hint: str | None = None,
    ) -> ExternalAccount:
        candidates = list(
            self._repository.find_candidates(
                user_id=user_id,
                organization_id=organization_id,
                provider=provider,
                account_hint=account_hint,
            )
        )
        if not candidates:
            raise LookupError("account_not_found")
        if len(candidates) > 1:
            raise AccountSelectionRequiredError("account_selection_required")
        return candidates[0]


class AuthorizationService:
    """Core authorization gate. Credential resolution must happen afterwards."""

    def __init__(self, permissions: PermissionRepository) -> None:
        self._permissions = permissions

    def authorize(
        self,
        *,
        context: AgentContext,
        account: ExternalAccount | None = None,
    ) -> AuthorizationDecision:
        capability = context.capability or ""
        action = context.action or ""

        if not self._permissions.has_capability_permission(
            user_id=context.user_id,
            capability=capability,
        ):
            return AuthorizationDecision(False, "capability_permission_denied", "authorization_denied")

        if account is not None and not self._permissions.has_account_access(
            organization_id=context.organization_id,
            user_id=context.user_id,
            account=account,
            capability=capability,
        ):
            return AuthorizationDecision(False, "account_access_denied", "authorization_denied")

        if context.target_resource and not self._permissions.has_resource_access(
            organization_id=context.organization_id,
            user_id=context.user_id,
            resource_id=context.target_resource,
            action=action,
        ):
            return AuthorizationDecision(False, "resource_access_denied", "authorization_denied")

        return AuthorizationDecision(True, "authorized", "allow")


class CredentialResolver:
    """Credential boundary. Call only after AuthorizationService returns ALLOW."""

    def __init__(self, repository: CredentialRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        decision: AuthorizationDecision,
        account: ExternalAccount,
    ) -> Any:
        if not decision.allowed:
            raise CoreAuthorizationError("credential_resolution_blocked")
        return self._repository.resolve_authorized_credential(account=account)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
