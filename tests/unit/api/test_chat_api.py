from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_agent_chat_contract_creates_conversation_id() -> None:
    response = client.post("/api/v1/agent/chat", json={"message": "Tôi có những tài khoản Google nào?"})
    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"]
    assert body["execution"]["account"]["status"] == "not_evaluated"
    assert body["execution"]["provider_called"] is False


def test_account_hint_requires_context() -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Dùng tài khoản abc@gmail.com", "account_hint": "abc@gmail.com"},
    )
    assert response.status_code == 400


def test_account_resolution_runtime_wiring(monkeypatch) -> None:
    def fake_resolve(*, user_id, organization_id, account_hint=None):
        assert (user_id, organization_id, account_hint) == ("user-1", "org-1", "abc@gmail.com")
        return {
            "status": "resolved",
            "provider": "google",
            "account_id": "01a0c387-8f30-767d-acb4-ccf9edc0f22b",
            "external_account_id": "google-1",
            "display_name": "Personal Google",
            "email": "abc@gmail.com",
            "provider_called": False,
        }

    monkeypatch.setattr("app.main.resolve_google_account", fake_resolve)
    response = client.post(
        "/api/v1/agent/chat",
        headers={"X-User-ID": "user-1", "X-Organization-ID": "org-1"},
        json={"message": "Dùng tài khoản abc@gmail.com", "account_hint": "abc@gmail.com"},
    )
    assert response.status_code == 200
    assert response.json()["execution"]["account"]["status"] == "resolved"


def test_authorization_runtime_wiring(monkeypatch) -> None:
    def fake_resolve(*, user_id, organization_id, account_hint=None):
        return {
            "status": "resolved",
            "provider": "google",
            "account_id": "01a0c387-8f30-767d-acb4-ccf9edc0f22b",
            "external_account_id": "google-1",
            "display_name": "Personal Google",
            "email": "abc@gmail.com",
            "provider_called": False,
        }

    def fake_authorize(**kwargs):
        assert kwargs["user_id"] == "user-1"
        assert kwargs["organization_id"] == "org-1"
        assert kwargs["capability"] == "calendar.read"
        assert kwargs["account"].id == "01a0c387-8f30-767d-acb4-ccf9edc0f22b"
        return {"status": "allow", "code": "allow", "reason": "authorized", "provider_called": False}

    monkeypatch.setattr("app.main.resolve_google_account", fake_resolve)
    monkeypatch.setattr("app.main.authorize_request", fake_authorize)
    response = client.post(
        "/api/v1/agent/chat",
        headers={"X-User-ID": "user-1", "X-Organization-ID": "org-1"},
        json={
            "message": "Đọc lịch",
            "account_hint": "abc@gmail.com",
            "capability": "calendar.read",
        },
    )
    assert response.status_code == 200
    assert response.json()["execution"]["authorization"]["status"] == "allow"


def test_classify_scheduling_request():
    from app.api.chat import classify_chat_request
    from app.api.schemas import ChatRequest

    intent, capability, action = classify_chat_request(
        ChatRequest(message="Tìm thời gian trống 1 tiếng ngày mai")
    )
    assert (intent, capability, action) == ("calendar", "calendar.read", "schedule")
