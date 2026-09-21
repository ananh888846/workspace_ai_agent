from app.application.core_runtime import ExternalAccount
from app.infrastructure.database.repositories.permissions import PostgresPermissionRepository


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.executed = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        self.executed = (query, params)

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.cursor_instance = FakeCursor(row)

    def cursor(self):
        return self.cursor_instance


def test_capability_permission_uses_role_permission_mapping():
    connection = FakeConnection((True,))
    repo = PostgresPermissionRepository(connection)

    assert repo.has_capability_permission(
        user_id="user-1",
        capability="calendar.read",
    ) is True

    query, params = connection.cursor_instance.executed
    assert "role_permissions" in query
    assert params == ["user-1", "calendar", "read"]


def test_account_access_does_not_touch_credentials():
    connection = FakeConnection((True,))
    repo = PostgresPermissionRepository(connection)
    account = ExternalAccount(
        id="acc-1",
        user_id="user-1",
        provider="google",
        account_type="oauth",
        external_account_id="google-1",
        email="a@example.com",
    )

    assert repo.has_account_access(
        organization_id="org-1",
        user_id="user-1",
        account=account,
        capability="calendar.read",
    ) is True

    query, _ = connection.cursor_instance.executed
    assert "account_credentials" not in query
