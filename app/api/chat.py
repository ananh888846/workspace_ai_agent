from __future__ import annotations

from uuid import uuid4

from app.api.schemas import ChatRequest, ChatResponse
from app.application.core_runtime import (
    AccountResolver,
    AccountSelectionRequiredError,
    AgentContext,
    AuthorizationDecision,
    AuthorizationService,
    CredentialResolver,
    ExternalAccount,
)
from app.infrastructure.database.connection import database_connection
from app.infrastructure.database.repositories.accounts import PostgresAccountRepository
from app.infrastructure.database.repositories.permissions import PostgresPermissionRepository
from app.infrastructure.database.repositories.credentials import PostgresCredentialRepository


def classify_chat_request(request: ChatRequest) -> tuple[str, str | None, str | None]:
    """Phân loại intent Calendar V1 ở lớp HTTP runtime trước khi resolve account."""
    if request.capability:
        action = request.action or ("read" if request.capability == "calendar.read" else "write")
        return "calendar", request.capability, action

    text = request.message.casefold()
    read_words = ("lịch", "calendar", "cuộc hẹn", "sự kiện", "agenda", "schedule")
    write_words = ("tạo lịch", "tạo cuộc hẹn", "đặt lịch", "thêm lịch", "thêm cuộc hẹn", "sửa lịch", "sửa cuộc hẹn", "cập nhật lịch", "xóa lịch", "xóa cuộc hẹn", "huỷ lịch", "hủy lịch")

    if not any(word in text for word in read_words):
        return "not_classified", None, None
    if any(word in text for word in write_words):
        return "calendar", "calendar.write", "write"
    return "calendar", "calendar.read", "read"


def build_chat_response(request: ChatRequest) -> ChatResponse:
    conversation_id = request.conversation_id or str(uuid4())
    return ChatResponse(
        status="ok",
        conversation_id=conversation_id,
        message="Backend đã phân loại yêu cầu.",
        execution={
            "intent": classify_chat_request(request)[0],
            "capability": classify_chat_request(request)[1],
            "action": classify_chat_request(request)[2],
            "account": {"status": "not_evaluated", "hint": request.account_hint},
            "authorization": {"status": "not_evaluated"},
            "provider_called": False,
        },
    )


def resolve_google_account(
    *, user_id: str, organization_id: str, account_hint: str | None = None
) -> dict:
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
            return {
                "status": "account_selection_required",
                "provider": "google",
                "provider_called": False,
            }
        except LookupError as exc:
            return {
                "status": str(exc),
                "provider": "google",
                "provider_called": False,
            }

    return _account_result(account)


def _account_result(account: ExternalAccount) -> dict:
    return {
        "status": "resolved",
        "provider": account.provider,
        "account_id": account.id,
        "external_account_id": account.external_account_id,
        "display_name": account.display_name,
        "email": account.email,
        "account_state": account.status,
        "provider_called": False,
    }


def authorize_request(
    *,
    user_id: str,
    organization_id: str,
    capability: str,
    action: str | None = None,
    account: ExternalAccount | None = None,
    target_resource: str | None = None,
) -> dict:
    context = AgentContext(
        request_id=str(uuid4()),
        organization_id=organization_id,
        user_id=user_id,
        capability=capability,
        action=action or capability.partition(".")[2],
        target_account=account.id if account else None,
        target_resource=target_resource,
    )
    with database_connection() as connection:
        service = AuthorizationService(PostgresPermissionRepository(connection))
        decision = service.authorize(context=context, account=account)

    return {
        "status": "allow" if decision.allowed else "deny",
        "code": decision.code,
        "reason": decision.reason,
        "provider_called": False,
    }


def resolve_google_credential(
    *, account: ExternalAccount, authorization: dict
) -> dict:
    """Kiểm tra credential sau khi Authorization đã cho phép."""

    if authorization.get("status") != "allow":
        return {
            "status": "not_evaluated",
            "provider_called": False,
        }

    with database_connection() as connection:
        resolver = CredentialResolver(
            PostgresCredentialRepository(connection)
        )
        decision = AuthorizationDecision(
            allowed=True,
            reason="authorized",
            code="allow",
        )
        result = resolver.resolve(
            decision=decision,
            account=account,
        )

    if result.status == "ready":
        return {
            "status": "ready",
            "credential_type": result.credential_type,
            "expires_at": (
                result.expires_at.isoformat()
                if result.expires_at is not None
                else None
            ),
            "scopes": result.scopes,
            "provider_called": False,
        }

    return {
        "status": "oauth_required",
        "code": "oauth_required",
        "reason": "credential_not_ready",
        "provider_called": False,
    }
