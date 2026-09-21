from __future__ import annotations

import pytest

from app.application.core_runtime import (
    AccountResolver,
    AccountSelectionRequiredError,
    AgentContext,
    AuthorizationService,
    CredentialResolver,
    ExternalAccount,
)


class FakeAccounts:
    def __init__(self, accounts):
        self.accounts = accounts
        self.calls = 0

    def find_candidates(self, **kwargs):
        self.calls += 1
        return self.accounts


class FakePermissions:
    def __init__(self, capability=True, account=True, resource=True):
        self.capability = capability
        self.account = account
        self.resource = resource
        self.credential_calls = 0

    def has_capability_permission(self, **kwargs):
        return self.capability

    def has_account_access(self, **kwargs):
        return self.account

    def has_resource_access(self, **kwargs):
        return self.resource


class FakeCredentials:
    def __init__(self):
        self.calls = 0

    def resolve_authorized_credential(self, **kwargs):
        self.calls += 1
        return "credential-context"


def account():
    return ExternalAccount(
        id="acc-1",
        user_id="user-1",
        provider="google",
        account_type="google",
        external_account_id="google-1",
    )


def test_account_resolver_never_needs_credentials():
    repo = FakeAccounts([account()])
    resolver = AccountResolver(repo)

    result = resolver.resolve(
        user_id="user-1",
        organization_id="org-1",
        provider="google",
    )

    assert result.id == "acc-1"
    assert repo.calls == 1


def test_multiple_accounts_require_explicit_selection():
    repo = FakeAccounts([account(), account().__class__(
        id="acc-2",
        user_id="user-1",
        provider="google",
        account_type="google",
        external_account_id="google-2",
    )])

    with pytest.raises(AccountSelectionRequiredError, match="account_selection_required"):
        AccountResolver(repo).resolve(
            user_id="user-1",
            organization_id="org-1",
            provider="google",
        )


def test_denied_authorization_blocks_credential_resolution():
    permissions = FakePermissions(capability=False)
    credentials = FakeCredentials()
    auth = AuthorizationService(permissions)
    decision = auth.authorize(
        context=AgentContext(
            request_id="req-1",
            organization_id="org-1",
            user_id="user-1",
            capability="calendar.read",
            action="list_events",
        ),
        account=account(),
    )

    assert decision.allowed is False
    with pytest.raises(Exception, match="credential_resolution_blocked"):
        CredentialResolver(credentials).resolve(
            decision=decision,
            account=account(),
        )
    assert credentials.calls == 0


def test_allow_then_credential_resolution():
    permissions = FakePermissions()
    credentials = FakeCredentials()
    auth = AuthorizationService(permissions)
    decision = auth.authorize(
        context=AgentContext(
            request_id="req-2",
            organization_id="org-1",
            user_id="user-1",
            capability="calendar.read",
            action="list_events",
        ),
        account=account(),
    )

    assert decision.allowed is True
    assert CredentialResolver(credentials).resolve(
        decision=decision,
        account=account(),
    ) == "credential-context"
    assert credentials.calls == 1
