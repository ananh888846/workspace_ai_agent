from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


class _FakeRuntime:
    def run(self, *, request, context):
        return {
            "status": "ok",
            "conversation_id": request.conversation_id or "conv-test",
            "message": "ok",
            "execution": {
                "intent": "calendar",
                "capability": "calendar.read",
                "action": "read",
                "provider_called": False,
            },
        }


def test_chat_returns_structured_success_and_request_id(monkeypatch):
    monkeypatch.setattr("app.api.security.get_settings", lambda: type("S", (), {"agent_server_token": "test-secret"})())

    import app.main as main_module

    monkeypatch.setattr(main_module, "_agent_runtime", _FakeRuntime())
    client = TestClient(app, headers={"Host": "127.0.0.1"})
    request_id = "123e4567-e89b-12d3-a456-426614174000"

    response = client.post(
        "/api/v1/agent/chat",
        headers={
            "Authorization": "Bearer test-secret",
            "X-Request-Id": request_id,
            "X-User-Id": "user-100",
            "X-Organization-Id": "org-10",
        },
        json={"message": "Đọc lịch"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["request_id"] == request_id


def test_chat_auth_failure_uses_structured_error(monkeypatch):
    monkeypatch.setattr("app.api.security.get_settings", lambda: type("S", (), {"agent_server_token": "test-secret"})())

    client = TestClient(app)
    request_id = "123e4567-e89b-12d3-a456-426614174000"

    response = client.post(
        "/api/v1/agent/chat",
        headers={
            "Authorization": "Bearer wrong-secret",
            "X-Request-Id": request_id,
            "X-User-Id": "user-100",
            "X-Organization-Id": "org-10",
        },
        json={"message": "Đọc lịch"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "SERVER_AUTHENTICATION_FAILED"
    assert body["request_id"] == request_id
