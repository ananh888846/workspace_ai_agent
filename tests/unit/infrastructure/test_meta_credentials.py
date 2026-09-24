from __future__ import annotations

import json

from cryptography.fernet import Fernet

from app.application.core_runtime import (
    AgentContext,
    AuthorizationDecision,
    CredentialResolver,
    ExternalAccount,
)
from app.infrastructure.database.repositories.meta_credentials import (
    PostgresMetaCredentialRepository,
)
from app.providers.meta.credentials import MetaCredentialContext


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        self.calls.append((query, params))

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.cursor_instance = FakeCursor(row)

    def cursor(self):
        return self.cursor_instance


def test_meta_repository_is_provider_scoped(monkeypatch):
    key = Fernet.generate_key().decode("ascii")
    encrypted = Fernet(key.encode("ascii")).encrypt(
        json.dumps({"access_token": "thread-token"}).encode("utf-8")
    )
    connection = FakeConnection(("threads_access_token", encrypted, None, ["threads_basic"]))

    class Settings:
        credential_encryption_key = key

    monkeypatch.setattr(
        "app.infrastructure.database.repositories.meta_credentials.get_settings",
        lambda: Settings(),
    )

    account = ExternalAccount(
        id="account-1",
        user_id="user-1",
        provider="threads",
        account_type="social",
        external_account_id="threads-user-1",
    )
    result = PostgresMetaCredentialRepository(connection).resolve_authorized_credential(
        account=account
    )

    assert result.status == "ready"
    assert isinstance(result.credential_context, MetaCredentialContext)
    assert result.credential_context.access_token == "thread-token"
    assert connection.cursor_instance.calls[0][1] == ["account-1", "threads"]


def test_missing_meta_credential_returns_oauth_required(monkeypatch):
    connection = FakeConnection(None)
    account = ExternalAccount(
        id="account-1",
        user_id="user-1",
        provider="threads",
        account_type="social",
        external_account_id="threads-user-1",
    )

    result = PostgresMetaCredentialRepository(connection).resolve_authorized_credential(
        account=account
    )

    assert result.status == "oauth_required"


def test_credential_resolver_blocks_denied_authorization():
    class ForbiddenRepository:
        called = False

        def resolve_authorized_credential(self, *, account):
            self.called = True
            raise AssertionError("credential repository must not be called")

    repository = ForbiddenRepository()
    resolver = CredentialResolver(repository)
    account = ExternalAccount(
        id="account-1",
        user_id="user-1",
        provider="threads",
        account_type="social",
        external_account_id="threads-user-1",
    )

    try:
        resolver.resolve(
            decision=AuthorizationDecision(
                allowed=False,
                reason="account_access_denied",
                code="authorization_denied",
            ),
            account=account,
        )
    except PermissionError as exc:
        assert str(exc) == "credential_resolution_blocked"
    else:
        raise AssertionError("denied authorization must block credential resolution")

    assert repository.called is False
