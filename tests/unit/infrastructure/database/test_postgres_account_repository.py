from __future__ import annotations

from app.infrastructure.database.repositories.accounts import PostgresAccountRepository


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.executed = (query, params)

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.cursor_obj = FakeCursor(rows)

    def cursor(self):
        return self.cursor_obj


def test_postgres_account_repository_maps_account_metadata_without_credentials():
    connection = FakeConnection([
        (
            "acc-1",
            "user-1",
            "google",
            "google",
            "google-1",
            "Personal Google",
            "user@example.com",
            "active",
            None,
            None,
        )
    ])

    accounts = PostgresAccountRepository(connection).find_candidates(
        user_id="user-1",
        organization_id="org-1",
        provider="google",
    )

    assert len(accounts) == 1
    assert accounts[0].account.id == "acc-1"
    assert accounts[0].account.external_account_id == "google-1"
    assert accounts[0].account.email == "user@example.com"
    assert accounts[0].access_mode == "owner"
    assert "account_credentials" not in connection.cursor_obj.executed[0]
    assert connection.cursor_obj.executed[1] == ["org-1", "user-1", "google", "user-1"]


def test_account_hint_is_exact_and_parameterized():
    connection = FakeConnection([])

    PostgresAccountRepository(connection).find_candidates(
        user_id="user-1",
        organization_id="org-1",
        provider="google",
        account_hint="acc-2",
    )

    query, params = connection.cursor_obj.executed
    assert "ua.id::text = %s" in query
    assert "ua.external_account_id = %s" in query
    assert "ua.email = %s" in query
    assert params[-3:] == ["acc-2", "acc-2", "acc-2"]


def test_account_repository_returns_grant_metadata_without_credentials():
    connection = FakeConnection([
        (
            "acc-2", "owner-1", "google", "google", "google-2",
            "Shared Google", "shared@example.com", "active",
            "grant-1", {"capabilities": ["calendar.read"]},
        )
    ])

    accounts = PostgresAccountRepository(connection).find_candidates(
        user_id="grantee-1",
        organization_id="org-1",
        provider="google",
    )

    assert accounts[0].access_mode == "grant"
    assert accounts[0].account_grant_id == "grant-1"
    assert accounts[0].grant_scope == {"capabilities": ["calendar.read"]}
    assert accounts[0].organization_id == "org-1"


def test_account_repository_returns_grant_metadata_without_credentials():
    connection = FakeConnection([
        (
            "acc-2",
            "owner-1",
            "google",
            "google",
            "google-2",
            "Shared Google",
            "shared@example.com",
            "active",
            "grant-1",
            {"capabilities": ["calendar.read"]},
        )
    ])

    accounts = PostgresAccountRepository(connection).find_candidates(
        user_id="grantee-1",
        organization_id="org-1",
        provider="google",
    )

    assert accounts[0].access_mode == "grant"
    assert accounts[0].account_grant_id == "grant-1"
    assert accounts[0].grant_scope == {"capabilities": ["calendar.read"]}
    assert accounts[0].organization_id == "org-1"
    assert "account_credentials" not in connection.cursor_obj.executed[0]
