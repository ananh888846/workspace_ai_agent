from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

from cryptography.fernet import Fernet

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
    assert "encrypted_value" in connection.cursor_instance.query


def test_active_credential_is_ready_without_returning_secret(monkeypatch):
    expires_at = datetime.now(timezone.utc)
    key = Fernet.generate_key()
    payload = {
        "token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }
    encrypted_value = Fernet(key).encrypt(json.dumps(payload).encode("utf-8"))
    monkeypatch.setattr(
        "app.infrastructure.database.repositories.credentials.get_settings",
        lambda: SimpleNamespace(google_credential_encryption_key=key.decode("ascii")),
    )
    connection = FakeConnection(
        ("oauth2", encrypted_value, expires_at, ["calendar.readonly"])
    )

    result = PostgresCredentialRepository(connection).resolve_authorized_credential(
        account=_account()
    )

    assert result.status == "ready"
    assert result.credential_type == "oauth2"
    assert result.expires_at == expires_at
    assert result.scopes == ["calendar.readonly"]
    assert result.credential_context is not None
    assert "encrypted_value" in connection.cursor_instance.query
