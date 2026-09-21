from __future__ import annotations

from uuid import uuid4

from app.api.schemas import ChatRequest, ChatResponse
from app.application.core_runtime import AccountResolver, AccountSelectionRequiredError
from app.infrastructure.database.connection import database_connection
from app.infrastructure.database.repositories.accounts import PostgresAccountRepository


def build_chat_response(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid4())
    return ChatResponse(
        status="ok",
        conversation_id=conversation_id,
        message="Backend HTTP contract đã nhận yêu cầu.",
        execution={
            "intent": "not_classified",
            "capability": None,
            "account": {"status": "not_evaluated", "hint": request.account_hint},
            "authorization": {"status": "not_evaluated"},
            "provider_called": False,
        },
    )


def resolve_google_account(*, user_id: str, organization_id: str, account_hint: str | None = None) -> dict:
    with database_connection() as connection:
        resolver = AccountResolver(PostgresAccountRepository(connection))
        try:
            account = resolver.resolve(
                user_id=user_id,
                organization_id=organization_id,
                provider="google",
                account_hint=account_hint,
            )
        except AccountSelectionRequiredError:
            return {"status": "account_selection_required", "provider": "google", "provider_called": False}
        except LookupError as exc:
            return {"status": str(exc), "provider": "google", "provider_called": False}

    return {
        "status": "resolved",
        "provider": account.provider,
        "account_id": account.id,
        "external_account_id": account.external_account_id,
        "display_name": account.display_name,
        "email": account.email,
        "provider_called": False,
    }
