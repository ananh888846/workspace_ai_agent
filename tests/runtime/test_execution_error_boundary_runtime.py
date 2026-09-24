import os
from types import SimpleNamespace

os.environ["AGENT_SERVER_TOKEN"] = "test-agent-server-token"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(*, user_id: str, organization_id: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer test-agent-server-token",
        "X-Request-Id": "11111111-1111-4111-8111-111111111111",
        "X-User-ID": user_id,
        "X-Organization-ID": organization_id,
    }


def _resolved_account() -> dict:
    return {
        "status": "resolved",
        "provider": "google",
        "account_id": "01a0c387-8f30-767d-acb4-ccf9edc0f22b",
        "external_account_id": "google-runtime-test",
        "display_name": "Runtime Test Account",
        "email": "runtime-test@example.com",
        "account_state": "active",
        "provider_called": False,
    }


def _patch_authorized_runtime(monkeypatch, *, credential_status: str = "ready") -> None:
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account",
        lambda **kwargs: _resolved_account(),
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.authorize_request",
        lambda **kwargs: {
            "status": "allow",
            "code": "allow",
            "reason": "authorized",
            "provider_called": False,
        },
    )

    class FakeCredentialResolver:
        def __init__(self, repository):
            self.repository = repository

        def resolve(self, *, decision, account):
            return SimpleNamespace(
                status=credential_status,
                credential_type="oauth" if credential_status == "ready" else None,
                expires_at=None,
                scopes=[],
                credential_context=object() if credential_status == "ready" else None,
            )

    monkeypatch.setattr(
        "app.application.capabilities.calendar.CredentialResolver",
        FakeCredentialResolver,
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_credential",
        lambda **kwargs: (
            {
                "status": "ready",
                "credential_type": "oauth",
                "expires_at": None,
                "scopes": [],
                "provider_called": False,
            }
            if credential_status == "ready"
            else {
                "status": "oauth_required",
                "code": "oauth_required",
                "reason": "credential_not_ready",
                "provider_called": False,
            }
        ),
    )


def test_runtime_account_not_found_error_boundary(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account",
        lambda **kwargs: {
            "status": "account_not_found",
            "provider": "google",
            "provider_called": False,
        },
    )

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(user_id="runtime-user", organization_id="runtime-org"),
        json={
            "message": "Đọc lịch",
            "capability": "calendar.read",
            "action": "read",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["execution"]["account"]["status"] == "account_not_found"
    assert body["execution"]["account"]["provider_called"] is False
    assert body["execution"]["authorization"]["status"] == "not_evaluated"
    assert body["execution"]["provider_called"] is False
    assert "calendar" not in body


def test_runtime_authorization_denied_error_boundary(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account",
        lambda **kwargs: _resolved_account(),
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.authorize_request",
        lambda **kwargs: {
            "status": "deny",
            "code": "authorization_denied",
            "reason": "capability_permission_denied",
            "provider_called": False,
        },
    )

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(user_id="runtime-user", organization_id="runtime-org"),
        json={
            "message": "Đọc lịch",
            "capability": "calendar.read",
            "action": "read",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["account"]["status"] == "resolved"
    assert body["execution"]["authorization"]["status"] == "authorization_denied"
    assert body["execution"]["authorization"]["provider_called"] is False
    assert body["execution"]["provider_called"] is False
    assert body["execution"]["credential"]["status"] == "not_evaluated"
    assert "calendar" not in body


def test_runtime_oauth_required_error_boundary(monkeypatch) -> None:
    _patch_authorized_runtime(monkeypatch, credential_status="oauth_required")

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(user_id="runtime-user", organization_id="runtime-org"),
        json={
            "message": "Đọc lịch",
            "capability": "calendar.read",
            "action": "read",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["execution"]["account"]["status"] == "resolved"
    assert body["execution"]["authorization"]["status"] == "allow"
    assert body["execution"]["credential"]["status"] == "oauth_required"
    assert body["execution"]["credential"]["provider_called"] is False
    assert body["execution"]["provider_called"] is False
    assert "calendar" not in body


def test_runtime_validation_error_boundary_never_calls_provider(monkeypatch) -> None:
    _patch_authorized_runtime(monkeypatch)

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(user_id="runtime-user", organization_id="runtime-org"),
        json={
            "message": "Đọc lịch",
            "capability": "calendar.read",
            "action": "read",
            "start": "2026-09-25T12:00:00+07:00",
            "end": "2026-09-25T11:00:00+07:00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calendar"]["status"] == "validation_error"
    assert body["calendar"]["error"] == "end_must_be_after_start"
    assert body["calendar"]["provider_called"] is False
    assert body["execution"]["provider_called"] is False
    assert body["execution"]["account"]["provider_called"] is False
    assert body["execution"]["authorization"]["provider_called"] is False
    assert body["execution"]["credential"]["provider_called"] is False


def test_runtime_provider_error_boundary_marks_provider_called(monkeypatch) -> None:
    _patch_authorized_runtime(monkeypatch)

    def fake_calendar_read(**kwargs):
        raise RuntimeError("simulated provider timeout")

    monkeypatch.setattr("app.application.capabilities.calendar.execute_google_calendar_read", fake_calendar_read)

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(user_id="runtime-user", organization_id="runtime-org"),
        json={
            "message": "Đọc lịch",
            "capability": "calendar.read",
            "action": "read",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calendar"]["status"] == "provider_error"
    assert body["calendar"]["error"] == "simulated provider timeout"
    assert body["calendar"]["provider_called"] is True
    assert body["execution"]["provider_called"] is True
    assert body["execution"]["account"]["provider_called"] is True
    assert body["execution"]["authorization"]["provider_called"] is True
    assert body["execution"]["credential"]["provider_called"] is True
