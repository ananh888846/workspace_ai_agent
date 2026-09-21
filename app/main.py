from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.api.chat import (
    authorize_request,
    build_chat_response,
    resolve_google_account,
)
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount

app = FastAPI(title="Workspace AI Agent", version="2.1-phase2c")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None
    capability: str | None = None
    action: str | None = None
    target_resource: str | None = None


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
            user_id=x_user_id,  # type: ignore[arg-type]
            organization_id=x_organization_id,  # type: ignore[arg-type]
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
            status="active",
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

    return body
