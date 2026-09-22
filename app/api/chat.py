from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.api.schemas import ChatRequest, ChatResponse
from app.core.datetime import to_utc, to_vietnam_time, utc_now
from app.application.core_runtime import AccountResolver, AccountSelectionRequiredError, AgentContext, AuthorizationDecision, AuthorizationService, CredentialResolver, ExternalAccount
from app.infrastructure.database.connection import database_connection
from app.infrastructure.database.repositories.accounts import PostgresAccountRepository
from app.infrastructure.database.repositories.permissions import PostgresPermissionRepository
from app.infrastructure.database.repositories.credentials import PostgresCredentialRepository
from app.tools.registry import CalendarToolRegistry


def _repair_mojibake(value: str | None) -> str | None:
    """Khôi phục chuỗi UTF-8 bị giải mã nhầm thành Latin-1/Windows-1252.

    Chỉ sửa khi chuỗi chứa các dấu hiệu mojibake phổ biến; chuỗi Unicode bình
    thường được giữ nguyên. Đây là lớp bảo vệ cuối trước khi gửi text tới Google.
    """
    if value is None or not any(marker in value for marker in ("Ã", "Â", "â", "ð", "�")):
        return value
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return repaired


def classify_chat_request(request: ChatRequest) -> tuple[str, str | None, str | None]:
    if request.capability:
        action = request.action or ("read" if request.capability == "calendar.read" else "write")
        return "calendar", request.capability, action
    text = request.message.casefold()
    read_words = ("lịch", "calendar", "cuộc hẹn", "sự kiện", "agenda", "schedule")
    write_words = ("tạo lịch", "tạo cuộc hẹn", "đặt lịch", "thêm lịch", "thêm cuộc hẹn", "sửa lịch", "sửa cuộc hẹn", "cập nhật lịch", "xóa lịch", "xóa cuộc hẹn", "xoá lịch", "xoá cuộc hẹn", "huỷ lịch", "hủy lịch")
    if not any(word in text for word in read_words):
        return "not_classified", None, None
    if any(word in text for word in write_words):
        return "calendar", "calendar.write", request.action or _infer_write_action(text)
    return "calendar", "calendar.read", "read"


def _infer_write_action(text: str) -> str:
    if any(word in text for word in ("xóa", "xoá", "hủy", "huỷ")):
        return "delete"
    if any(word in text for word in ("sửa", "cập nhật")):
        return "update"
    return "create"


def build_chat_response(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid4())
    intent, capability, action = classify_chat_request(request)
    return ChatResponse(status="ok", conversation_id=conversation_id, message="Backend đã phân loại yêu cầu.", execution={"intent": intent, "capability": capability, "action": action, "account": {"status": "not_evaluated", "hint": request.account_hint}, "authorization": {"status": "not_evaluated"}, "provider_called": False})


def resolve_google_account(*, user_id: str, organization_id: str, account_hint: str | None = None) -> dict:
    with database_connection() as connection:
        resolver = AccountResolver(PostgresAccountRepository(connection))
        try:
            account = resolver.resolve(user_id=user_id, organization_id=organization_id, provider="google", account_hint=account_hint)
        except AccountSelectionRequiredError:
            return {"status": "account_selection_required", "provider": "google", "provider_called": False}
        except LookupError as exc:
            return {"status": str(exc), "provider": "google", "provider_called": False}
    return _account_result(account)


def _account_result(account: ExternalAccount) -> dict:
    return {"status": "resolved", "provider": account.provider, "account_id": account.id, "external_account_id": account.external_account_id, "display_name": account.display_name, "email": account.email, "account_state": account.status, "provider_called": False}


def authorize_request(*, user_id: str, organization_id: str, capability: str, action: str | None = None, account: ExternalAccount | None = None, target_resource: str | None = None) -> dict:
    context = AgentContext(request_id=str(uuid4()), organization_id=organization_id, user_id=user_id, capability=capability, action=action or capability.partition(".")[2], target_account=account.id if account else None, target_resource=target_resource)
    with database_connection() as connection:
        decision = AuthorizationService(PostgresPermissionRepository(connection)).authorize(context=context, account=account)
    return {"status": "allow" if decision.allowed else "deny", "code": decision.code, "reason": decision.reason, "provider_called": False}


def resolve_google_credential(*, account: ExternalAccount, authorization: dict) -> dict:
    if authorization.get("status") != "allow":
        return {"status": "not_evaluated", "provider_called": False}
    with database_connection() as connection:
        result = CredentialResolver(PostgresCredentialRepository(connection)).resolve(decision=AuthorizationDecision(allowed=True, reason="authorized", code="allow"), account=account)
    if result.status == "ready":
        return {"status": "ready", "credential_type": result.credential_type, "expires_at": result.expires_at.isoformat() if result.expires_at else None, "scopes": result.scopes, "provider_called": False}
    return {"status": "oauth_required", "code": "oauth_required", "reason": "credential_not_ready", "provider_called": False}


def _parse_client_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return to_utc(parsed)


def _google_datetime(value: str) -> dict[str, str]:
    dt = _parse_client_datetime(value)
    return {"dateTime": dt.isoformat().replace("+00:00", "Z"), "timeZone": "UTC"}


def _event_to_response(event: object) -> dict:
    return {"id": event.id, "summary": event.summary, "description": event.description, "location": event.location, "start": event.start, "end": event.end, "status": event.status, "html_link": event.html_link}


def execute_google_calendar_read(*, account: ExternalAccount, credential_resolution: object) -> dict:
    credential_context = getattr(credential_resolution, "credential_context", None)
    if credential_context is None:
        raise RuntimeError("google_credential_context_missing")
    now = to_vietnam_time(utc_now())
    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
    time_max = time_min + timedelta(days=1)
    tool = CalendarToolRegistry().resolve(capability="calendar.read", provider=account.provider, action="list_events")
    events = tool.execute("list_events", credential_context=credential_context, calendar_id=account.external_account_id, time_min=time_min.isoformat(), time_max=time_max.isoformat(), max_results=50)
    return {"status": "ok", "action": "list_events", "calendar_id": account.external_account_id, "events": [_event_to_response(event) for event in events], "provider_called": True}


def execute_google_calendar_write(*, account: ExternalAccount, credential_resolution: object, action: str, event_id: str | None = None, summary: str | None = None, start: str | None = None, end: str | None = None, description: str | None = None, location: str | None = None, confirmed: bool = False) -> dict:
    """Calendar Write V1: create/update/delete sau Authorization + credential resolution."""
    credential_context = getattr(credential_resolution, "credential_context", None)
    if credential_context is None:
        raise RuntimeError("google_credential_context_missing")
    if action == "delete" and not confirmed:
        return {"status": "confirmation_required", "action": "delete_event", "provider_called": False}
    if action in {"update", "delete"} and not event_id:
        return {"status": "validation_error", "error": "event_id_required", "provider_called": False}
    if action == "create" and (not summary or not start or not end):
        return {"status": "validation_error", "error": "summary_start_end_required", "provider_called": False}
    for datetime_value in (start, end):
        if datetime_value is not None:
            try:
                _parse_client_datetime(datetime_value)
            except (TypeError, ValueError):
                return {"status": "validation_error", "error": "datetime_must_be_iso8601_with_timezone", "provider_called": False}
    provider_action = {"create": "create_event", "update": "update_event", "delete": "delete_event"}.get(action)
    if provider_action is None:
        raise ValueError("unsupported_calendar_write_action")
    tool = CalendarToolRegistry().resolve(capability="calendar.write", provider=account.provider, action=provider_action)
    if action == "delete":
        tool.execute("delete_event", credential_context=credential_context, calendar_id=account.external_account_id, event_id=event_id)
        return {"status": "ok", "action": "delete_event", "event_id": event_id, "provider_called": True}
    event: dict = {}
    repaired_summary = _repair_mojibake(summary)
    repaired_description = _repair_mojibake(description)
    repaired_location = _repair_mojibake(location)
    if repaired_summary is not None:
        event["summary"] = repaired_summary
    if repaired_description is not None:
        event["description"] = repaired_description
    if repaired_location is not None:
        event["location"] = repaired_location
    if start is not None:
        event["start"] = _google_datetime(start)
    if end is not None:
        event["end"] = _google_datetime(end)
    if action == "create":
        result = tool.execute("create_event", credential_context=credential_context, calendar_id=account.external_account_id, event=event)
    else:
        result = tool.execute("update_event", credential_context=credential_context, calendar_id=account.external_account_id, event_id=event_id, event=event)
    return {"status": "ok", "action": provider_action, "event": _event_to_response(result), "provider_called": True}
