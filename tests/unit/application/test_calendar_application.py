from __future__ import annotations

import pytest

from app.application.calendar import (
    AuthorizationDecision,
    CalendarAccount,
    CalendarApplicationService,
    CalendarRequestContext,
)


class FakeAccountResolver:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, **kwargs):
        self.calls += 1
        return CalendarAccount(id="acc-1", provider="google")


class FakeAuthorization:
    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.calls = 0

    def authorize(self, **kwargs):
        self.calls += 1
        return AuthorizationDecision(
            allowed=self.allowed,
            reason=None if self.allowed else "authorization_denied",
        )


class FakeCredentialResolver:
    def __init__(self) -> None:
        self.calls = 0

    def resolve(self, **kwargs):
        self.calls += 1
        return object()


class FakeTool:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, action, **kwargs):
        self.calls += 1
        return {"action": action}


class FakeToolResolver:
    def __init__(self, tool: FakeTool) -> None:
        self.tool = tool
        self.calls = 0

    def resolve(self, **kwargs):
        self.calls += 1
        return self.tool


def make_service(allowed: bool):
    account = FakeAccountResolver()
    authorization = FakeAuthorization(allowed)
    credential = FakeCredentialResolver()
    tool = FakeTool()
    tool_resolver = FakeToolResolver(tool)
    service = CalendarApplicationService(
        account_resolver=account,
        authorization_service=authorization,
        credential_resolver=credential,
        tool_resolver=tool_resolver,
    )
    return service, account, authorization, credential, tool_resolver, tool


def test_denied_authorization_does_not_resolve_credential_or_tool():
    service, account, authorization, credential, tool_resolver, tool = make_service(False)

    with pytest.raises(PermissionError, match="authorization_denied"):
        service.execute(
            context=CalendarRequestContext(
                organization_id="org-1",
                user_id="user-1",
                capability="calendar.read",
                action="list_events",
            ),
            action="list_events",
        )

    assert account.calls == 1
    assert authorization.calls == 1
    assert credential.calls == 0
    assert tool_resolver.calls == 0
    assert tool.calls == 0


def test_allowed_authorization_resolves_credential_then_tool():
    service, _, _, credential, tool_resolver, tool = make_service(True)

    result = service.execute(
        context=CalendarRequestContext(
            organization_id="org-1",
            user_id="user-1",
            capability="calendar.read",
            action="list_events",
        ),
        action="list_events",
        calendar_id="primary",
    )

    assert result == {"action": "list_events"}
    assert credential.calls == 1
    assert tool_resolver.calls == 1
    assert tool.calls == 1
