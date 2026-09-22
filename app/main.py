from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from app.api.chat import (
    authorize_request,
    build_chat_response,
    classify_chat_request,
    execute_google_calendar_read,
    execute_google_calendar_write,
    resolve_google_account,
    resolve_google_credential,
)
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount
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

def _natural_language_calendar_start(message: str, explicit_start: str | None) -> str | None:
    """Chuẩn hóa start từ câu tiếng Việt khi request chưa truyền start rõ ràng."""
    if explicit_start:
        return explicit_start

    normalized = message.casefold()
    markers = (
        "hôm nay", "ngày mai", "ngày kia", "mai", "tuần", "thứ ",
        "giờ", "h", "phút", "tiếng", "/",
    )
    if not any(marker in normalized for marker in markers):
        return None

    try:
        parsed = CalendarDateTimeParser().parse(message)
    except ValueError:
        return None
    return parsed.value.isoformat()


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
    needs_runtime_context = bool(payload.account_hint or payload.capability or payload.target_resource or payload.action)
    if needs_runtime_context and (not x_user_id or not x_organization_id):
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required for runtime authorization")

    request = ChatRequest(message=payload.message, conversation_id=payload.conversation_id, account_hint=payload.account_hint, capability=payload.capability, action=payload.action, target_resource=payload.target_resource)
    body = asdict(build_chat_response(request))
    intent, capability, action = classify_chat_request(request)
    body["execution"]["intent"] = intent
    body["execution"]["capability"] = capability
    body["execution"]["action"] = action

    if intent != "calendar" or capability is None:
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")
    if not x_user_id or not x_organization_id:
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required for Calendar runtime")

    execution_account = resolve_google_account(user_id=x_user_id, organization_id=x_organization_id, account_hint=payload.account_hint)
    body["execution"]["account"] = execution_account
    if execution_account["status"] != "resolved":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    account = ExternalAccount(id=execution_account["account_id"], user_id=x_user_id, provider=execution_account["provider"], account_type="oauth", external_account_id=execution_account["external_account_id"], display_name=execution_account["display_name"], email=execution_account["email"], status=execution_account.get("account_state", "active"))
    authorization = authorize_request(user_id=x_user_id, organization_id=x_organization_id, capability=capability, action=action, account=account, target_resource=payload.target_resource)
    body["execution"]["authorization"] = authorization
    if authorization.get("status") != "allow":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    from app.application.core_runtime import AuthorizationDecision, CredentialResolver
    from app.infrastructure.database.connection import database_connection
    from app.infrastructure.database.repositories.credentials import PostgresCredentialRepository
    with database_connection() as connection:
        credential_result = CredentialResolver(PostgresCredentialRepository(connection)).resolve(decision=AuthorizationDecision(allowed=True, reason="authorized", code="allow"), account=account)

    body["execution"]["credential"] = resolve_google_credential(account=account, authorization=authorization)
    if credential_result.status != "ready":
        return JSONResponse(content=body, media_type="application/json; charset=utf-8")

    try:
        if capability == "calendar.read" and action == "read":
            body["calendar"] = execute_google_calendar_read(account=account, credential_resolution=credential_result)
        elif capability == "calendar.write" and action in {"create", "update", "delete"}:
            natural_start = _natural_language_calendar_start(payload.message, payload.start)
            body["execution"]["natural_language_datetime"] = {
                "status": "resolved" if natural_start else "not_used",
                "start": natural_start,
                "timezone": "Asia/Ho_Chi_Minh" if natural_start else None,
            }
            body["calendar"] = execute_google_calendar_write(account=account, credential_resolution=credential_result, action=action, event_id=payload.event_id, summary=payload.summary, start=natural_start, end=payload.end, description=payload.description, location=payload.location, confirmed=payload.confirmed)
        else:
            body["calendar"] = {"status": "unsupported_action", "action": action, "provider_called": False}
        provider_called = body["calendar"].get("provider_called", False)
        body["execution"]["provider_called"] = provider_called
        body["execution"]["account"]["provider_called"] = provider_called
        body["execution"]["authorization"]["provider_called"] = provider_called
        body["execution"]["credential"]["provider_called"] = provider_called
    except Exception as exc:
        body["calendar"] = {"status": "provider_error", "error": str(exc), "provider_called": True}
        body["execution"]["provider_called"] = True
    return JSONResponse(content=body, media_type="application/json; charset=utf-8")
