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

    monkeypatch.setattr("app.application.capabilities.calendar.resolve_google_account", fake_resolve)
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

    monkeypatch.setattr("app.application.capabilities.calendar.resolve_google_account", fake_resolve)
    monkeypatch.setattr("app.application.capabilities.calendar.authorize_request", fake_authorize)
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


def test_classify_natural_meeting_write_requests() -> None:
    from app.api.chat import classify_chat_request
    from app.api.schemas import ChatRequest

    cases = {
        "Tạo cuộc họp ngày mai": ("calendar", "calendar.write", "create"),
        "Tạo meeting ngày mai": ("calendar", "calendar.write", "create"),
        "Sửa cuộc họp ngày mai": ("calendar", "calendar.write", "update"),
        "Xóa cuộc họp ngày mai": ("calendar", "calendar.write", "delete"),
        "Đọc cuộc họp ngày mai": ("calendar", "calendar.read", "read"),
    }

    for message, expected in cases.items():
        assert classify_chat_request(ChatRequest(message=message)) == expected


def test_natural_language_scheduling_enters_runtime(monkeypatch) -> None:
    calls = []

    def fake_resolve(*, user_id, organization_id, account_hint=None):
        calls.append((user_id, organization_id, account_hint))
        return {"status": "not_found", "provider_called": False}

    monkeypatch.setattr("app.application.capabilities.calendar.resolve_google_account", fake_resolve)
    response = client.post(
        "/api/v1/agent/chat",
        headers={
            "X-User-ID": "01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc",
            "X-Organization-ID": "01a0c387-8eaa-7147-8cf8-5e284268b30a",
        },
        json={"message": "Tìm thời gian trống 1 tiếng ngày mai"},
    )
    assert response.status_code == 200
    assert calls == [(
        "01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc",
        "01a0c387-8eaa-7147-8cf8-5e284268b30a",
        None,
    )]
    assert response.json()["execution"]["intent"] == "calendar"
    assert response.json()["execution"]["action"] == "schedule"

    
def test_calendar_read_uses_explicit_date_range(monkeypatch) -> None:
    from types import SimpleNamespace
    from app.api.chat import execute_google_calendar_read
    from app.application.core_runtime import ExternalAccount

    captured = {}

    class FakeTool:
        def execute(self, action, **kwargs):
            captured.update(kwargs)
            return []

    monkeypatch.setattr("app.api.chat.CalendarToolRegistry.resolve", lambda self, **kwargs: FakeTool())
    account = ExternalAccount(
        id="01a0c387-8f30-767d-acb4-ccf9edc0f22b",
        user_id="01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc",
        provider="google", account_type="oauth",
        external_account_id="ananh888846@gmail.com",
        display_name="Calendar", email=None, status="active",
    )
    credential = SimpleNamespace(credential_context=object())
    result = execute_google_calendar_read(
        account=account, credential_resolution=credential,
        start="2026-09-24T00:00:00+07:00",
        end="2026-09-25T00:00:00+07:00",
    )
    assert result["status"] == "ok"
    assert captured["time_min"] == "2026-09-23T17:00:00+00:00"
    assert captured["time_max"] == "2026-09-24T17:00:00+00:00"
    assert result["requested_start"] == "2026-09-24T00:00:00+07:00"
    assert result["requested_end"] == "2026-09-25T00:00:00+07:00"


def test_calendar_read_start_only_defaults_to_one_day(monkeypatch) -> None:
    from types import SimpleNamespace
    from app.api.chat import execute_google_calendar_read
    from app.application.core_runtime import ExternalAccount

    captured = {}

    class FakeTool:
        def execute(self, action, **kwargs):
            captured.update(kwargs)
            return []

    monkeypatch.setattr("app.api.chat.CalendarToolRegistry.resolve", lambda self, **kwargs: FakeTool())
    account = ExternalAccount(
        id="01a0c387-8f30-767d-acb4-ccf9edc0f22b",
        user_id="01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc",
        provider="google", account_type="oauth",
        external_account_id="ananh888846@gmail.com",
        display_name="Calendar", email=None, status="active",
    )
    credential = SimpleNamespace(credential_context=object())
    result = execute_google_calendar_read(
        account=account, credential_resolution=credential,
        start="2026-09-24T13:00:00+07:00",
    )
    assert result["status"] == "ok"
    assert captured["time_min"] == "2026-09-24T06:00:00+00:00"
    assert captured["time_max"] == "2026-09-25T06:00:00+00:00"


def test_calendar_read_rejects_invalid_range(monkeypatch) -> None:
    from types import SimpleNamespace
    from app.api.chat import execute_google_calendar_read
    from app.application.core_runtime import ExternalAccount

    monkeypatch.setattr("app.api.chat.CalendarToolRegistry.resolve", lambda self, **kwargs: None)
    account = ExternalAccount(
        id="01a0c387-8f30-767d-acb4-ccf9edc0f22b",
        user_id="01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc",
        provider="google", account_type="oauth",
        external_account_id="ananh888846@gmail.com",
        display_name="Calendar", email=None, status="active",
    )
    credential = SimpleNamespace(credential_context=object())
    result = execute_google_calendar_read(
        account=account, credential_resolution=credential,
        start="2026-09-25T00:00:00+07:00",
        end="2026-09-24T00:00:00+07:00",
    )
    assert result == {
        "status": "validation_error",
        "action": "list_events",
        "error": "end_must_be_after_start",
        "provider_called": False,
    }

 
def test_calendar_write_accepts_recurrence_argument(monkeypatch) -> None:
    from types import SimpleNamespace
    from app.api.chat import execute_google_calendar_write
    from app.application.core_runtime import ExternalAccount

    captured = {}

    class FakeTool:
        def execute(self, action, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="event-1",
                summary="Họp",
                description=None,
                location=None,
                status="confirmed",
                html_link=None,
                start={"dateTime": "2026-09-24T02:00:00Z"},
                end={"dateTime": "2026-09-24T03:00:00Z"},
            )

    monkeypatch.setattr(
        "app.api.chat.CalendarToolRegistry.resolve",
        lambda self, **kwargs: FakeTool(),
    )
    account = ExternalAccount(
        id="account-1",
        user_id="user-1",
        provider="google",
        account_type="oauth",
        external_account_id="calendar-1",
        display_name="Calendar",
        email="abc@gmail.com",
        status="active",
    )
    credential = SimpleNamespace(credential_context=object())
    result = execute_google_calendar_write(
        account=account,
        credential_resolution=credential,
        action="create",
        summary="Họp",
        start="2026-09-24T09:00:00+07:00",
        end="2026-09-24T10:00:00+07:00",
        recurrence="FREQ=DAILY;COUNT=2",
    )

    assert result["status"] == "ok"
    assert captured["event"]["recurrence"] == ["RRULE:FREQ=DAILY;COUNT=2"]


def test_credential_result_can_be_reused_without_second_resolution() -> None:
    from app.api.chat import resolve_google_credential

    class FakeCredential:
        status = "ready"
        credential_type = "google_oauth"
        expires_at = None
        scopes = ["calendar"]

    result = resolve_google_credential(
        account=None,
        authorization={"status": "allow"},
        credential_resolution=FakeCredential(),
    )

    assert result["status"] == "ready"
    assert result["credential_type"] == "google_oauth"
    assert result["scopes"] == ["calendar"]
