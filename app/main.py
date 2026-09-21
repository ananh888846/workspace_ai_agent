from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.api.chat import build_chat_response, resolve_google_account
from app.api.schemas import ChatRequest

app = FastAPI(title="Workspace AI Agent", version="2.1-phase2b")


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/agent/chat")
def agent_chat(
    payload: AgentChatRequest,
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> dict:
    if payload.account_hint:
        if not x_user_id or not x_organization_id:
            raise HTTPException(
                status_code=400,
                detail="x_user_id and x_organization_id are required for account resolution",
            )
        execution = resolve_google_account(
            user_id=x_user_id,
            organization_id=x_organization_id,
            account_hint=payload.account_hint,
        )
        response = build_chat_response(
            ChatRequest(
                message=payload.message,
                conversation_id=payload.conversation_id,
                account_hint=payload.account_hint,
            )
        )
        body = asdict(response)
        body["execution"]["account"] = execution
        return body

    return asdict(
        build_chat_response(
            ChatRequest(
                message=payload.message,
                conversation_id=payload.conversation_id,
                account_hint=payload.account_hint,
            )
        )
    )
