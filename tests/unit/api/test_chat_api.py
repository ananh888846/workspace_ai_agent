from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_agent_chat_contract_creates_conversation_id() -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={"message": "Tôi có những tài khoản Google nào?"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["conversation_id"]
    assert body["execution"]["account"]["status"] == "not_evaluated"
    assert body["execution"]["authorization"]["status"] == "not_evaluated"
    assert body["execution"]["provider_called"] is False


def test_agent_chat_contract_preserves_conversation_and_account_hint() -> None:
    response = client.post(
        "/api/v1/agent/chat",
        json={
            "message": "Dùng tài khoản abc@gmail.com",
            "conversation_id": "phase2-contract-001",
            "account_hint": "abc@gmail.com",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["conversation_id"] == "phase2-contract-001"
    assert body["execution"]["account"]["hint"] == "abc@gmail.com"
