from __future__ import annotations

from uuid import uuid4

from app.api.schemas import ChatRequest, ChatResponse


def build_chat_response(request: ChatRequest) -> ChatResponse:
    """Phase 2A HTTP contract.

    No LLM, credential, tool, or provider call happens in this phase.
    """
    conversation_id = request.conversation_id or str(uuid4())
    return ChatResponse(
        status="ok",
        conversation_id=conversation_id,
        message="Backend HTTP contract đã nhận yêu cầu.",
        execution={
            "intent": "not_classified",
            "capability": None,
            "account": {
                "status": "not_evaluated",
                "hint": request.account_hint,
            },
            "authorization": {"status": "not_evaluated"},
            "provider_called": False,
        },
    )
