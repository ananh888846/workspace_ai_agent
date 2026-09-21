from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException\nfrom fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.chat import (
    authorize_request,
    build_chat_response,
    resolve_google_account,
    resolve_google_credential,
)
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount\nfrom app.infrastructure.oauth.google import GoogleOAuthService
from app.config.settings import get_settings

app = FastAPI(title="Workspace AI Agent", version="2.1-phase2c")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None
    capability: str | None = None
    action: str | None = None
    target_resource: str | None = None



@app.get("/auth/google/start")
def google_oauth_start(
    account_id: str,
    capability: str = "calendar.read",
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> RedirectResponse:
    """Tạo URL Google OAuth sau khi kiểm tra AccountResolver và Authorization."""
    if not x_user_id or not x_organization_id:
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required")
    if capability not in {"calendar.read", "calendar.write"}:
        raise HTTPException(status_code=400, detail="unsupported_calendar_capability")
    account = resolve_google_account(
        user_id=x_user_id,
        organization_id=x_organization_id,
        account_hint=account_id,
    )
    if account.get("status") != "resolved":
        raise HTTPException(status_code=404, detail=account.get("status", "account_not_found"))
    external_account = ExternalAccount(
        id=account["account_id"],
        user_id=x_user_id,
        provider=account["provider"],
        account_type="oauth",
        external_account_id=account["external_account_id"],
        display_name=account["display_name"],
        email=account["email"],
        status=account.get("account_state", "active"),
    )
    authorization = authorize_request(
        user_id=x_user_id,
        organization_id=x_organization_id,
        capability=capability,
        action="read" if capability == "calendar.read" else "write",
        account=external_account,
    )
    if authorization.get("status") != "allow":
        raise HTTPException(status_code=403, detail=authorization.get("reason", "authorization_denied"))
    scopes = (
        [get_settings().google_calendar_read_scope]
        if capability == "calendar.read"
        else [get_settings().google_calendar_write_scope]
    )
    try:
        url = GoogleOAuthService().authorization_url(
            account_id=account["account_id"],
            user_id=x_user_id,
            organization_id=x_organization_id,
            scopes=scopes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=302)


@app.get("/auth/google/callback")
def google_oauth_callback(code: str, state: str) -> dict:
    """Đổi authorization code lấy credential và lưu credential đã mã hóa."""
    try:
        oauth_state = GoogleOAuthService().handle_callback(code=code, state=state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "ok",
        "account_id": oauth_state.account_id,
        "organization_id": oauth_state.organization_id,
        "message": "Google OAuth hoàn tất.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/agent/chat")
def agent_chat(
    payload: AgentChatRequest,
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> dict:
    needs_runtime_context = bool(
        payload.account_hint or payload.capability or payload.target_resource
    )
    if needs_runtime_context and (not x_user_id or not x_organization_id):
        raise HTTPException(
            status_code=400,
            detail="x_user_id and x_organization_id are required for runtime authorization",
        )

    request = ChatRequest(
        message=payload.message,
        conversation_id=payload.conversation_id,
        account_hint=payload.account_hint,
        capability=payload.capability,
        action=payload.action,
        target_resource=payload.target_resource,
    )
    body = asdict(build_chat_response(request))

    account = None
    if payload.account_hint:
        execution_account = resolve_google_account(
            user_id=x_user_id,  # Bỏ qua kiểm tra kiểu vì header đã được kiểm tra ở trên.
            organization_id=x_organization_id,  # Bỏ qua kiểm tra kiểu vì header đã được kiểm tra ở trên.
            account_hint=payload.account_hint,
        )
        body["execution"]["account"] = execution_account
        if execution_account["status"] != "resolved":
            return body
        account = ExternalAccount(
            id=execution_account["account_id"],
            user_id=x_user_id,
            provider=execution_account["provider"],
            account_type="oauth",
            external_account_id=execution_account["external_account_id"],
            display_name=execution_account["display_name"],
            email=execution_account["email"],
            status=execution_account.get("account_state", "active"),
        )

    if payload.capability:
        authorization = authorize_request(
            user_id=x_user_id,  # type: ignore[arg-type]
            organization_id=x_organization_id,  # type: ignore[arg-type]
            capability=payload.capability,
            action=payload.action,
            account=account,
            target_resource=payload.target_resource,
        )
        body["execution"]["authorization"] = authorization
        if authorization.get("status") == "allow" and account is not None:
            body["execution"]["credential"] = resolve_google_credential(
                account=account,
                authorization=authorization,
            )

    return body
