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
from app.services.calendar_free_busy import BusyPeriod, CalendarConflictDetector
from app.graphs.scheduling import SchedulingGraphDependencies, run_scheduling_graph


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
    scheduling_words = (
        "tìm thời gian", "tìm giờ", "tìm lịch", "xếp lịch", "sắp xếp lịch",
        "lịch trống", "khung giờ", "slot", "thời gian phù hợp",
    )
    if any(word in text for word in scheduling_words) and not any(word in text for word in write_words):
        return "calendar", "calendar.read", "schedule"
    if not any(word in text for word in read_words):
        return "not_classified", None, None
    free_busy_words = ("rảnh", "bận", "trống", "free busy", "free/busy", "availability")
    if any(word in text for word in free_busy_words) and not any(word in text for word in write_words):
        return "calendar", "calendar.read", "free_busy"
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
    """Chuẩn hóa event provider để response hiển thị theo GMT+7."""
    def _display_datetime(value: dict | None) -> dict | None:
        if not value or not value.get("dateTime"):
            return value
        parsed = datetime.fromisoformat(str(value["dateTime"]).replace("Z", "+00:00"))
        local = to_vietnam_time(parsed)
        return {**value, "dateTime": local.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"}

    return {
        "id": event.id,
        "summary": event.summary,
        "description": event.description,
        "location": event.location,
        "start": _display_datetime(event.start),
        "end": _display_datetime(event.end),
        "status": event.status,
        "html_link": event.html_link,
    }


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





def execute_google_calendar_scheduling(
    *,
    account: ExternalAccount,
    credential_resolution: object,
    search_start: str | None,
    search_end: str | None,
    duration_minutes: int,
    max_results: int = 5,
) -> dict:
    """Tìm slot rảnh qua Scheduling Graph sau Authorization và credential resolution."""
    credential_context = getattr(credential_resolution, "credential_context", None)
    if credential_context is None:
        raise RuntimeError("google_credential_context_missing")
    if not search_start or not search_end:
        return {
            "status": "validation_error",
            "error": "search_start_search_end_required",
            "provider_called": False,
        }
    try:
        requested_start = _parse_client_datetime(search_start)
        requested_end = _parse_client_datetime(search_end)
    except (TypeError, ValueError):
        return {
            "status": "validation_error",
            "error": "datetime_must_be_iso8601_with_timezone",
            "provider_called": False,
        }
    if duration_minutes <= 0:
        return {
            "status": "validation_error",
            "error": "duration_minutes_must_be_positive",
            "provider_called": False,
        }
    if requested_end <= requested_start:
        return {
            "status": "validation_error",
            "error": "search_end_must_be_after_search_start",
            "provider_called": False,
        }

    def resolve_calendar(state: dict) -> list[str]:
        return [account.external_account_id]

    def get_free_busy(state: dict, calendar_ids: list[str]) -> list[BusyPeriod]:
        tool = CalendarToolRegistry().resolve(
            capability="calendar.read",
            provider=account.provider,
            action="free_busy",
        )
        provider_data = tool.execute(
            "free_busy",
            credential_context=credential_context,
            calendar_ids=calendar_ids,
            time_min=requested_start.isoformat().replace("+00:00", "Z"),
            time_max=requested_end.isoformat().replace("+00:00", "Z"),
            time_zone="Asia/Ho_Chi_Minh",
        )
        return _busy_periods_from_provider(provider_data)

    result = run_scheduling_graph(
        search_start=requested_start,
        search_end=requested_end,
        duration_minutes=duration_minutes,
        max_results=max_results,
        dependencies=SchedulingGraphDependencies(
            resolve_calendar=resolve_calendar,
            get_free_busy=get_free_busy,
        ),
    )
    return {
        "status": result["status"],
        "action": "schedule",
        "calendar_ids": result.get("calendar_ids", []),
        "search_start": to_vietnam_time(requested_start).isoformat(),
        "search_end": to_vietnam_time(requested_end).isoformat(),
        "duration_minutes": duration_minutes,
        "timezone": "Asia/Ho_Chi_Minh",
        "busy": [
            {
                "calendar_id": period.calendar_id,
                "start": to_vietnam_time(period.start).isoformat(),
                "end": to_vietnam_time(period.end).isoformat(),
            }
            for period in result.get("busy_periods", [])
        ],
        "available_slots": [
            {
                "start": to_vietnam_time(slot.start).isoformat(),
                "end": to_vietnam_time(slot.end).isoformat(),
            }
            for slot in result.get("available_slots", [])
        ],
        "provider_called": True,
    }


def _busy_periods_from_provider(data: dict[str, list[dict[str, str]]]) -> list[BusyPeriod]:
    periods: list[BusyPeriod] = []
    for calendar_id, busy_items in data.items():
        for item in busy_items:
            periods.append(
                BusyPeriod(
                    calendar_id=calendar_id,
                    start=_parse_client_datetime(item["start"]),
                    end=_parse_client_datetime(item["end"]),
                )
            )
    return periods


def execute_google_calendar_free_busy(
    *, account: ExternalAccount, credential_resolution: object, start: str | None, end: str | None
) -> dict:
    """Lấy Free/Busy và kiểm tra conflict cho khoảng thời gian được yêu cầu."""
    credential_context = getattr(credential_resolution, "credential_context", None)
    if credential_context is None:
        raise RuntimeError("google_credential_context_missing")
    if not start or not end:
        return {"status": "validation_error", "error": "start_end_required_for_free_busy", "provider_called": False}
    try:
        requested_start = _parse_client_datetime(start)
        requested_end = _parse_client_datetime(end)
    except (TypeError, ValueError):
        return {"status": "validation_error", "error": "datetime_must_be_iso8601_with_timezone", "provider_called": False}
    if requested_end <= requested_start:
        return {"status": "validation_error", "error": "end_must_be_after_start", "provider_called": False}

    tool = CalendarToolRegistry().resolve(capability="calendar.read", provider=account.provider, action="free_busy")
    provider_data = tool.execute(
        "free_busy",
        credential_context=credential_context,
        calendar_ids=[account.external_account_id],
        time_min=requested_start.isoformat().replace("+00:00", "Z"),
        time_max=requested_end.isoformat().replace("+00:00", "Z"),
        time_zone="Asia/Ho_Chi_Minh",
    )
    busy_periods = _busy_periods_from_provider(provider_data)
    conflict_result = CalendarConflictDetector().detect(
        requested_start=requested_start,
        requested_end=requested_end,
        busy_periods=busy_periods,
    )
    return {
        "status": "conflict" if conflict_result.has_conflict else "free",
        "action": "free_busy",
        "calendar_ids": [account.external_account_id],
        "requested_start": to_vietnam_time(requested_start).isoformat(),
        "requested_end": to_vietnam_time(requested_end).isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
        "busy": [
            {"calendar_id": period.calendar_id, "start": to_vietnam_time(period.start).isoformat(), "end": to_vietnam_time(period.end).isoformat()}
            for period in busy_periods
        ],
        "conflicts": [
            {"calendar_id": conflict.calendar_id, "start": to_vietnam_time(conflict.start).isoformat(), "end": to_vietnam_time(conflict.end).isoformat()}
            for conflict in conflict_result.conflicts
        ],
        "provider_called": True,
    }
