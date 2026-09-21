from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from app.providers.google.calendar.adapter import CalendarEvent


@dataclass(frozen=True)
class CalendarAccount:
    """Resolved external Google account metadata; never contains secrets."""

    id: str
    provider: str
    display_name: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class CalendarRequestContext:
    organization_id: str
    user_id: str
    capability: str
    action: str
    account_hint: str | None = None


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str | None = None


class CalendarAccountResolver(Protocol):
    def resolve(
        self, *, user_id: str, organization_id: str, account_hint: str | None
    ) -> CalendarAccount:
        """Resolve account metadata only. Must not load credentials."""


class CalendarAuthorizationService(Protocol):
    def authorize(
        self,
        *,
        context: CalendarRequestContext,
        account: CalendarAccount,
        resource_id: str | None = None,
    ) -> AuthorizationDecision:
        ...


class CalendarCredentialResolver(Protocol):
    def resolve(self, *, account: CalendarAccount) -> Any:
        """Return a short-lived credential context after authorization."""


class CalendarTool(Protocol):
    def execute(self, action: str, *, credential_context: Any, **kwargs: Any) -> Any:
        ...


class CalendarToolResolver(Protocol):
    def resolve(self, *, capability: str, provider: str, action: str) -> CalendarTool:
        ...


class CalendarApplicationService:
    """Application boundary for Google Calendar operations.

    The order is intentional:
    AccountResolver -> Authorization -> CredentialResolver -> ToolResolver -> Tool.

    No provider call is possible when authorization is denied.
    """

    def __init__(
        self,
        *,
        account_resolver: CalendarAccountResolver,
        authorization_service: CalendarAuthorizationService,
        credential_resolver: CalendarCredentialResolver,
        tool_resolver: CalendarToolResolver,
    ) -> None:
        self._account_resolver = account_resolver
        self._authorization_service = authorization_service
        self._credential_resolver = credential_resolver
        self._tool_resolver = tool_resolver

    def execute(
        self,
        *,
        context: CalendarRequestContext,
        action: str,
        account_hint: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> Any:
        if action not in {
            "list_events",
            "get_event",
            "create_event",
            "update_event",
            "delete_event",
        }:
            raise ValueError(f"Unsupported calendar action: {action}")

        capability = (
            "calendar.read"
            if action in {"list_events", "get_event"}
            else "calendar.write"
        )

        request_context = CalendarRequestContext(
            organization_id=context.organization_id,
            user_id=context.user_id,
            capability=capability,
            action=action,
            account_hint=account_hint or context.account_hint,
        )

        account = self._account_resolver.resolve(
            user_id=request_context.user_id,
            organization_id=request_context.organization_id,
            account_hint=request_context.account_hint,
        )

        decision = self._authorization_service.authorize(
            context=request_context,
            account=account,
            resource_id=resource_id,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason or "authorization_denied")

        credential_context = self._credential_resolver.resolve(account=account)

        tool = self._tool_resolver.resolve(
            capability=capability,
            provider=account.provider,
            action=action,
        )
        return tool.execute(
            action,
            credential_context=credential_context,
            **kwargs,
        )
