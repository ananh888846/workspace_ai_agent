from __future__ import annotations

from dataclasses import asdict
import re

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.api.chat import (
    authorize_request,
    build_chat_response,
    classify_chat_request,
    execute_google_calendar_read,
    execute_google_calendar_free_busy,
    execute_google_calendar_scheduling,
    execute_google_calendar_write,
    resolve_google_account,
    resolve_google_credential,
)
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount
from app.application.execution_boundary import enforce_result_boundary
from app.application.execution_contract import build_execution_contract, normalize_result_status
from app.infrastructure.oauth.google import GoogleOAuthService
from app.config.settings import get_settings
from app.services.calendar_datetime import CalendarDateTimeParser

app = FastAPI(title="Workspace AI Agent", version="2.1-phase2c")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None
    capability: str | None = None
    action: str | None = None
    target_resource: str | None = None
    event_id: str | None = None
    summary: str | None = None
    start: str | None = None
    end: str | None = None
    description: str | None = None
    location: str | None = None
    confirmed: bool = False
    search_start: str | None = None
    search_end: str | None = None
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    max_results: int = Field(default=5, ge=1, le=20)


def _natural_language_calendar_start(message: str, explicit_start: str | None) -> str | None:
    """Chuẩn hóa start từ câu tiếng Việt khi request chưa truyền start rõ ràng."""
    if explicit_start:
        return explicit_start

    normalized = message.casefold()
    markers = (
        "hôm nay", "ngày mai", "ngày kia", "mai", "tuần", "thứ ",
        "giờ", "phút", "tiếng", "/",
    )
    has_clock_time = re.search(r"\b\d{1,2}(?::\d{2}|h(?:\s*\d{2})?)\b", normalized) is not None
    if not any(marker in normalized for marker in markers) and not has_clock_time:
        return None

    try:
        parsed = CalendarDateTimeParser().parse(message)
    except ValueError:
        return None
    return parsed.value.isoformat()


def _execution_contract(*, intent: str, capability: str | None, action: str | None) -> dict:
    """Tạo execution state từ contract chuẩn thay vì tự dựng shape riêng."""
    return build_execution_contract(
        intent=intent,
        capability=capability,
        action=action,
    )


def _normalize_execution_statuses(execution: dict) -> None:
    """Chuẩn hóa các status runtime qua Execution Contract trước khi trả API."""
    for key in ("account", "authorization", "credential"):
        section = execution.get(key)
        if isinstance(section, dict) and isinstance(section.get("status"), str):
            section["status"] = normalize_result_status(section["status"])


@app.get("/auth/google/start")
def google_oauth_start(account_id: str, capability: str = "calendar.read", x_user_id: str | None = Header(default=None), x_organization_id: str | None = Header(default=None)) -> RedirectResponse:
    if not x_user_id or not x_organization_id:
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required")
    if capability not in {"calendar.read", "calendar.write"}:
        raise HTTPException(status_code=400, detail="unsupported_calendar_capability")
    account = resolve_google_account(user_id=x_user_id, organization_id=x_organization_id, account_hint=account_id)
    if account.get("status") != "resolved":
        raise HTTPException(status_code=404, detail=account.get("status", "account_not_found"))
    external_account = ExternalAccount(id=account["account_id"], user_id=x_user_id, provider=account["provider"], account_type="oauth", external_account_id=account["external_account_id"], display_name=account["display_name"], email=account["email"], status=account.get("account_state", "active"))
    authorization = authorize_request(user_id=x_user_id, organization_id=x_organization_id, capability=capability, action="read" if capability == "calendar.read" else "write", account=external_account)
    if authorization.get("status") != "allow":
        raise HTTPException(status_code=403, detail=authorization.get("reason", "authorization_denied"))
    scopes = [get_settings().google_calendar_read_scope] if capability == "calendar.read" else [get_settings().google_calendar_write_scope]
    try:
        url = GoogleOAuthService().authorization_url(account_id=account["account_id"], user_id=x_user_id, organization_id=x_organization_id, scopes=scopes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=302)


@app.get("/auth/google/callback")
def google_oauth_callback(code: str, state: str) -> dict:
    try:
        oauth_state = GoogleOAuthService().handle_callback(code=code, state=state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "account_id": oauth_state.account_id, "organization_id": oauth_state.organization_id, "message": "Google OAuth hoàn tất."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/agent/chat")
def agent_chat(payload: AgentChatRequest, x_user_id: str | None = Header(default=None), x_organization_id: str | None = Header(default=None)) -> dict:
    request = ChatRequest(message=payload.message, conversation_id=payload.conversation_id, account_hint=payload.account_hint, capability=payload.capability, action=payload.action, target_resource=payload.target_resource)
    body = asdict(build_chat_response(request))
    intent, capability, action = classify_chat_request(request)

    # Execution Contract V1 là source của truth cho runtime execution shape.
    body["execution"] = _execution_contract(intent=intent, capability=capability, action=action)

    # Request Calendar đã được phân loại phải đi vào runtime authorization,
    # kể cả khi client không truyền capability/action tường minh.
    needs_runtime_context = bool(
        payload.account_hint
        or payload.capability
        or payload.target_resource
        or payload.action
        or (intent == "calendar" and capability is not None)
    )
    if needs_runtime_context and (not x_user_id or not x_organization_id):
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required for runtime authorization")

    if not needs_runtime_context:
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")
    if not x_user_id or not x_organization_id:
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required for runtime authorization")

    execution_account = resolve_google_account(user_id=x_user_id, organization_id=x_organization_id, account_hint=payload.account_hint)
    body["execution"]["account"] = execution_account
    _normalize_execution_statuses(body["execution"])
    if execution_account["status"] != "resolved":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    if intent != "calendar" or capability is None:
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    account = ExternalAccount(id=execution_account["account_id"], user_id=x_user_id, provider=execution_account["provider"], account_type="oauth", external_account_id=execution_account["external_account_id"], display_name=execution_account["display_name"], email=execution_account["email"], status=execution_account.get("account_state", "active"))
    authorization = authorize_request(user_id=x_user_id, organization_id=x_organization_id, capability=capability, action=action, account=account, target_resource=payload.target_resource)
    body["execution"]["authorization"] = authorization
    _normalize_execution_statuses(body["execution"])
    if authorization.get("status") != "allow":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    from app.application.core_runtime import AuthorizationDecision, CredentialResolver
    from app.infrastructure.database.connection import database_connection
    from app.infrastructure.database.repositories.credentials import PostgresCredentialRepository
    with database_connection() as connection:
        credential_result = CredentialResolver(PostgresCredentialRepository(connection)).resolve(decision=AuthorizationDecision(allowed=True, reason="authorized", code="allow"), account=account)

    body["execution"]["credential"] = resolve_google_credential(account=account, authorization=authorization)
    _normalize_execution_statuses(body["execution"])
    if credential_result.status != "ready":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    try:
        if capability == "calendar.read" and action == "read":
            body["calendar"] = execute_google_calendar_read(account=account, credential_resolution=credential_result, start=payload.start, end=payload.end)
        elif capability == "calendar.read" and action == "schedule":
            body["calendar"] = execute_google_calendar_scheduling(account=account, credential_resolution=credential_result, search_start=payload.search_start or payload.start, search_end=payload.search_end or payload.end, duration_minutes=payload.duration_minutes, max_results=payload.max_results)
        elif capability == "calendar.read" and action == "free_busy":
            body["calendar"] = execute_google_calendar_free_busy(account=account, credential_resolution=credential_result, start=payload.start, end=payload.end)
        elif capability == "calendar.write" and action in {"create", "update", "delete"}:
            natural_start = _natural_language_calendar_start(payload.message, payload.start)
            body["execution"]["natural_language_datetime"] = {"status": "resolved" if natural_start else "not_used", "start": natural_start, "timezone": "Asia/Ho_Chi_Minh" if natural_start else None}
            body["calendar"] = execute_google_calendar_write(account=account, credential_resolution=credential_result, action=action, event_id=payload.event_id, summary=payload.summary, start=natural_start, end=payload.end, description=payload.description, location=payload.location, confirmed=payload.confirmed)
        else:
            body["calendar"] = {"status": "unsupported_action", "action": action, "provider_called": False}
    except ValueError as exc:
        # Không biến lỗi provider-boundary thành provider_error giả.
        if str(exc).startswith("provider_called_must_"):
            raise
        body["calendar"] = {"status": "validation_error", "error": str(exc), "provider_called": False}
    except Exception as exc:
        body["calendar"] = {"status": "provider_error", "error": str(exc), "provider_called": True}

    body["calendar"] = enforce_result_boundary(body["calendar"])
    provider_called = body["calendar"].get("provider_called", False)
    body["execution"]["provider_called"] = provider_called
    body["execution"]["account"]["provider_called"] = provider_called
    body["execution"]["authorization"]["provider_called"] = provider_called
    body["execution"]["credential"]["provider_called"] = provider_called
    return JSONResponse(content=body, media_type="application/json; charset=utf-8")
