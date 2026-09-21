from __future__ import annotations

from datetime import datetime, timezone

from app.application.core_runtime import ExternalAccount
from app.infrastructure.database.repositories.credentials import (
    PostgresCredentialRepository,
)


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.query = query
        self.params = params

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.cursor_instance = FakeCursor(row)

    def cursor(self):
        return self.cursor_instance


def _account() -> ExternalAccount:
    return ExternalAccount(
        id="acc-1",
        user_id="user-1",
        provider="google",
        account_type="google_calendar",
        external_account_id="google-1",
    )


def test_missing_credential_requires_oauth():
    connection = FakeConnection(None)

    result = PostgresCredentialRepository(connection).resolve_authorized_credential(
        account=_account()
    )

    assert result.status == "oauth_required"
    assert connection.cursor_instance.params == ["acc-1"]
    assert "encrypted_value" not in connection.cursor_instance.query


def test_active_credential_is_ready_without_returning_secret():
    expires_at = datetime.now(timezone.utc)
    connection = FakeConnection(("oauth2", expires_at, ["calendar.readonly"]))

    result = PostgresCredentialRepository(connection).resolve_authorized_credential(
        account=_account()
    )

    assert result.status == "ready"
    assert result.credential_type == "oauth2"
    assert result.expires_at == expires_at
    assert result.scopes == ["calendar.readonly"]
    assert "encrypted_value" not in connection.cursor_instance.query
