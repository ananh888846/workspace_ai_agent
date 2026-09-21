from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.api.chat import build_chat_response
from app.api.schemas import ChatRequest

app = FastAPI(
    title="Workspace AI Agent",
    version="2.1-phase2",
    description="Phase 2 backend HTTP contract for the Agent chat runtime.",
)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/agent/chat")
def agent_chat(payload: AgentChatRequest) -> dict:
    response = build_chat_response(
        ChatRequest(
            message=payload.message,
            conversation_id=payload.conversation_id,
            account_hint=payload.account_hint,
        )
    )
    return asdict(response)
