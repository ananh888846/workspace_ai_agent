from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.chat import classify_chat_request
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount
from app.application.capabilities.calendar import calendar_handler
from app.agent_runtime.runtime import AgentRuntime, AgentRuntimeDependencies, AgentRuntimeState
from app.infrastructure.oauth.google import GoogleOAuthService
from app.config.settings import get_settings

app = FastAPI(title="Workspace AI Agent", version="2.1-phase3")


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
    recurrence: str | None = None


@app.get("/auth/google/start")
def google_oauth_start(
    account_id: str,
    capability: str = "calendar.read",
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> RedirectResponse:
    if not x_user_id or not x_organization_id:
        raise HTTPException(status_code=400, detail="x_user_id and x_organization_id are required")
    if capability not in {"calendar.read", "calendar.write"}:
        raise HTTPException(status_code=400, detail="unsupported_calendar_capability")
    account = calendar_handler.resolve_account_for_oauth(
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
    authorization = calendar_handler.authorize_for_oauth(
        user_id=x_user_id,
        organization_id=x_organization_id,
        capability=capability,
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


def _classify_agent_request(payload: AgentChatRequest) -> tuple[str, str | None, str | None]:
    request = ChatRequest(
        message=payload.message,
        conversation_id=payload.conversation_id,
        account_hint=payload.account_hint,
        capability=payload.capability,
        action=payload.action,
        target_resource=payload.target_resource,
    )
    return classify_chat_request(request)


_agent_runtime = AgentRuntime(
    AgentRuntimeDependencies(
        classify=_classify_agent_request,
        route_handlers={
            "calendar.read": calendar_handler.handle,
            "calendar.write": calendar_handler.handle,
            "default": calendar_handler.handle,
        },
    )
)


@app.post("/api/v1/agent/chat")
def agent_chat(
    payload: AgentChatRequest,
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> dict:
    context = {
        "user_id": x_user_id,
        "organization_id": x_organization_id,
    }
    return _agent_runtime.run(request=payload, context=context)
