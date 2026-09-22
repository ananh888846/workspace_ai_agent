from types import SimpleNamespace

from app.application.capabilities.calendar import CalendarHandler
from app.application.core_runtime import ExternalAccount
from app.api.schemas import ChatRequest


class Payload:
    message = "Đọc lịch"
    conversation_id = "test-calendar-handler"
    account_hint = "abc@gmail.com"
    capability = "calendar.read"
    action = "read"
    target_resource = None
    start = None
    end = None
    search_start = None
    search_end = None
    duration_minutes = 60
    max_results = 5
    event_id = None
    summary = None
    description = None
    location = None
    confirmed = False
    recurrence = None


def _state() -> dict:
    return {
        "request": Payload(),
        "context": {"user_id": "user-1", "organization_id": "org-1"},
        "intent": "calendar",
        "capability": "calendar.read",
        "action": "read",
    }


def test_calendar_handler_runs_application_boundary_in_order(monkeypatch) -> None:
    calls: list[str] = []

    account_result = {
        "status": "resolved",
        "provider": "google",
        "account_id": "account-1",
        "external_account_id": "calendar-1",
        "display_name": "Calendar",
        "email": "abc@gmail.com",
        "account_state": "active",
        "provider_called": False,
    }

    def fake_account(**kwargs):
        calls.append("account")
        return account_result.copy()

    def fake_authorize(**kwargs):
        calls.append("authorization")
        assert kwargs["resolved_account"] is None
        return {
            "status": "allow",
            "code": "allow",
            "reason": "authorized",
            "provider_called": False,
        }

    credential = SimpleNamespace(
        status="ready",
        credential_type="google_oauth",
        expires_at=None,
        scopes=["calendar"],
        credential_context=object(),
    )

    def fake_credential(**kwargs):
        calls.append("credential")
        return {
            "status": "ready",
            "credential_type": "google_oauth",
            "expires_at": None,
            "scopes": ["calendar"],
            "provider_called": False,
        }

    def fake_calendar(**kwargs):
        calls.append("calendar")
        return {
            "status": "ok",
            "action": "list_events",
            "events": [],
            "provider_called": True,
        }

    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account", fake_account
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.authorize_request", fake_authorize
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_credential", fake_credential
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.execute_google_calendar_read",
        fake_calendar,
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.CredentialResolver.resolve",
        lambda *args, **kwargs: (calls.append("credential_resolver") or credential),
    )

    result = CalendarHandler().handle(_state())

    assert result["calendar"]["status"] == "ok"
    assert calls == [
        "account",
        "authorization",
        "credential_resolver",
        "credential",
        "calendar",
    ]


def test_calendar_handler_denied_authorization_does_not_resolve_credential_or_provider(
    monkeypatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account",
        lambda **kwargs: {
            "status": "resolved",
            "provider": "google",
            "account_id": "account-1",
            "external_account_id": "calendar-1",
            "display_name": "Calendar",
            "email": "abc@gmail.com",
            "account_state": "active",
            "provider_called": False,
        },
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.authorize_request",
        lambda **kwargs: (
            calls.append("authorization")
            or {
                "status": "deny",
                "code": "authorization_denied",
                "reason": "denied",
                "provider_called": False,
            }
        ),
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.CredentialResolver.resolve",
        lambda *args, **kwargs: calls.append("credential"),
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.execute_google_calendar_read",
        lambda **kwargs: calls.append("provider"),
    )

    result = CalendarHandler().handle(_state())

    assert result["execution"]["authorization"]["status"] == "authorization_denied"
    assert calls == ["authorization"]


def test_calendar_handler_does_not_put_credentials_in_graph_state(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.application.capabilities.calendar.resolve_google_account",
        lambda **kwargs: {
            "status": "resolved",
            "provider": "google",
            "account_id": "account-1",
            "external_account_id": "calendar-1",
            "display_name": "Calendar",
            "email": "abc@gmail.com",
            "account_state": "active",
            "provider_called": False,
        },
    )
    monkeypatch.setattr(
        "app.application.capabilities.calendar.authorize_request",
        lambda **kwargs: {
            "status": "deny",
            "code": "authorization_denied",
            "reason": "denied",
            "provider_called": False,
        },
    )

    state = _state()
    CalendarHandler().handle(state)

    serialized = repr(state).casefold()
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "encrypted_value" not in serialized
