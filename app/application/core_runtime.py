from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence


class CoreAuthorizationError(PermissionError):
    """Được phát sinh khi capability được bảo vệ chưa được cấp quyền."""


class AccountSelectionRequiredError(RuntimeError):
    """Được phát sinh khi có nhiều account phù hợp nhưng chưa chọn account."""


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
class AccountCandidate:
    """Account metadata + access metadata; không chứa credential secret."""

    account: ExternalAccount
    access_mode: str
    account_grant_id: str | None = None
    organization_id: str | None = None
    grant_scope: dict[str, Any] | None = None


@dataclass(frozen=True)
class ResolvedAccount:
    """Account đã resolve, không chứa access token/refresh token/client secret."""

    account: ExternalAccount
    access_mode: str
    account_grant_id: str | None
    organization_id: str
    grant_scope: dict[str, Any] | None = None


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
    ) -> Sequence[AccountCandidate]:
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
        grant_scope: dict[str, Any] | None = None,
        access_mode: str | None = None,
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


@dataclass(frozen=True)
class CredentialResolution:
    """Kết quả kiểm tra trạng thái credential sau khi đã được authorization."""

    status: str
    credential_type: str | None = None
    expires_at: datetime | None = None
    scopes: Any | None = None
    credential_context: Any | None = None


class CredentialRepository(Protocol):
    def resolve_authorized_credential(self, *, account: ExternalAccount) -> CredentialResolution:
        ...


class AccountResolver:
    """Phân giải metadata tài khoản mà không truy cập credential."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        user_id: str,
        organization_id: str,
        provider: str,
        account_hint: str | None = None,
    ) -> ResolvedAccount:
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
        candidate = candidates[0]
        return ResolvedAccount(
            account=candidate.account,
            access_mode=candidate.access_mode,
            account_grant_id=candidate.account_grant_id,
            organization_id=candidate.organization_id or organization_id,
            grant_scope=candidate.grant_scope,
        )


class AuthorizationService:
    """Cổng authorization lõi; chỉ được phân giải credential sau bước này."""

    def __init__(self, permissions: PermissionRepository) -> None:
        self._permissions = permissions

    def authorize(
        self,
        *,
        context: AgentContext,
        account: ExternalAccount | None = None,
        resolved_account: ResolvedAccount | None = None,
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
            grant_scope=resolved_account.grant_scope if resolved_account else None,
            access_mode=resolved_account.access_mode if resolved_account else None,
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
    """Biên credential; chỉ được gọi sau khi AuthorizationService trả về ALLOW."""

    def __init__(self, repository: CredentialRepository) -> None:
        self._repository = repository

    def resolve(
        self,
        *,
        decision: AuthorizationDecision,
        account: ExternalAccount,
    ) -> CredentialResolution:
        if not decision.allowed:
            raise CoreAuthorizationError("credential_resolution_blocked")
        return self._repository.resolve_authorized_credential(account=account)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
