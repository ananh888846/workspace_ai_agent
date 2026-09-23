from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException

from app.api.chat import (
    authorize_request,
    build_chat_response,
    execute_google_calendar_free_busy,
    execute_google_calendar_read,
    execute_google_calendar_scheduling,
    execute_google_calendar_write,
    resolve_google_account,
    resolve_google_credential,
)
from app.api.schemas import ChatRequest
from app.application.core_runtime import AuthorizationDecision, CredentialResolver, ExternalAccount
from app.application.execution_boundary import enforce_result_boundary
from app.application.execution_contract import build_execution_contract, normalize_result_status
from app.agent_runtime.runtime import AgentRuntimeState
from app.infrastructure.database.connection import database_connection
from app.infrastructure.database.repositories.credentials import PostgresCredentialRepository
from app.services.calendar_datetime import CalendarDateTimeParser


class CalendarHandler:
    """Application Handler cho Calendar capability.

    Handler chịu trách nhiệm orchestration ở application boundary:
    Account -> Authorization -> Credential -> Calendar execution.
    Business logic vẫn nằm ở service/tool/provider hiện hữu.
    """

    def handle(self, state: AgentRuntimeState) -> dict[str, Any]:
        """Xử lý một Calendar route từ Agent Super-Graph."""
        payload = state["request"]
        context = state.get("context") or {}
        user_id = context.get("user_id")
        organization_id = context.get("organization_id")

        request = ChatRequest(
            message=payload.message,
            conversation_id=payload.conversation_id,
            account_hint=payload.account_hint,
            capability=payload.capability,
            action=payload.action,
            target_resource=payload.target_resource,
        )
        body = self._build_response(request, state)

        intent = state["intent"]
        capability = state.get("capability")
        action = state.get("action")
        needs_runtime_context = bool(
            payload.account_hint
            or payload.capability
            or payload.target_resource
            or payload.action
            or (intent == "calendar" and capability is not None)
        )

        if not needs_runtime_context:
            return body
        if not user_id or not organization_id:
            raise HTTPException(
                status_code=400,
                detail="x_user_id and x_organization_id are required for runtime authorization",
            )

        execution_account = resolve_google_account(
            user_id=user_id,
            organization_id=organization_id,
            account_hint=payload.account_hint,
        )
        resolved_account = execution_account.pop("_resolved_account", None)
        body["execution"]["account"] = execution_account
        self._normalize_execution_statuses(body["execution"])

        if execution_account["status"] != "resolved":
            return body
        if intent != "calendar" or capability is None:
            return body

        account = ExternalAccount(
            id=execution_account["account_id"],
            user_id=user_id,
            provider=execution_account["provider"],
            account_type="oauth",
            external_account_id=execution_account["external_account_id"],
            display_name=execution_account["display_name"],
            email=execution_account["email"],
            status=execution_account.get("account_state", "active"),
        )
        authorization = authorize_request(
            user_id=user_id,
            organization_id=organization_id,
            capability=capability,
            action=action,
            account=account,
            target_resource=payload.target_resource,
            resolved_account=resolved_account,
        )
        body["execution"]["authorization"] = authorization
        self._normalize_execution_statuses(body["execution"])
        if authorization.get("status") != "allow":
            return body

        with database_connection() as connection:
            credential_result = CredentialResolver(
                PostgresCredentialRepository(connection)
            ).resolve(
                decision=AuthorizationDecision(
                    allowed=True,
                    reason="authorized",
                    code="allow",
                ),
                account=account,
            )

        body["execution"]["credential"] = resolve_google_credential(
            account=account,
            authorization=authorization,
            credential_resolution=credential_result,
        )
        self._normalize_execution_statuses(body["execution"])
        if credential_result.status != "ready":
            # OAuth chưa sẵn sàng là lỗi trước provider: tuyệt đối không đánh dấu provider đã gọi.
            # Tạo dict mới để bảo đảm không có alias/reference nào làm thay đổi cờ sau đó.
            body["execution"]["credential"] = {
                **body["execution"]["credential"],
                "provider_called": False,
            }
            body["execution"]["provider_called"] = False
            return body

        calendar_result = self._execute_calendar(
            payload=payload,
            capability=capability,
            action=action,
            account=account,
            credential_result=credential_result,
        )
        natural_language_datetime = calendar_result.pop("_natural_language_datetime", None)
        if natural_language_datetime is not None:
            body["execution"]["natural_language_datetime"] = natural_language_datetime
        body["calendar"] = enforce_result_boundary(calendar_result)

        provider_called = body["calendar"].get("provider_called", False)
        for section in (
            body["execution"],
            body["execution"]["account"],
            body["execution"]["authorization"],
            body["execution"]["credential"],
        ):
            section["provider_called"] = provider_called

        return body

    @staticmethod
    def _build_response(request: ChatRequest, state: AgentRuntimeState) -> dict[str, Any]:
        """Tạo response envelope từ Execution Contract."""
        response = build_chat_response(request)
        body = {
            "status": response.status,
            "conversation_id": response.conversation_id,
            "message": response.message,
            "execution": response.execution,
            "request_id": (state.get("context") or {}).get("request_id"),
        }
        body["execution"] = build_execution_contract(
            intent=state["intent"],
            capability=state.get("capability"),
            action=state.get("action"),
        )
        return body

    @staticmethod
    def _normalize_execution_statuses(execution: dict[str, Any]) -> None:
        """Chuẩn hóa status của các boundary result."""
        for key in ("account", "authorization", "credential"):
            section = execution.get(key)
            if isinstance(section, dict) and isinstance(section.get("status"), str):
                section["status"] = normalize_result_status(section["status"])

    @staticmethod
    def _natural_language_calendar_start(
        message: str, explicit_start: str | None
    ) -> str | None:
        """Chuẩn hóa start từ câu tiếng Việt khi request chưa truyền start rõ ràng."""
        if explicit_start:
            return explicit_start

        normalized = message.casefold()
        markers = (
            "hôm nay",
            "ngày mai",
            "ngày kia",
            "mai",
            "tuần",
            "thứ ",
            "giờ",
            "phút",
            "tiếng",
            "/",
        )
        has_clock_time = (
            re.search(r"\b\d{1,2}(?::\d{2}|h(?:\s*\d{2})?)\b", normalized)
            is not None
        )
        if not any(marker in normalized for marker in markers) and not has_clock_time:
            return None

        try:
            parsed = CalendarDateTimeParser().parse(message)
        except ValueError:
            return None
        return parsed.value.isoformat()

    def _execute_calendar(
        self,
        *,
        payload: Any,
        capability: str,
        action: str | None,
        account: ExternalAccount,
        credential_result: object,
    ) -> dict[str, Any]:
        """Dispatch Calendar action tới execution function hiện hữu."""
        try:
            if capability == "calendar.read" and action == "read":
                return execute_google_calendar_read(
                    account=account,
                    credential_resolution=credential_result,
                    start=payload.start,
                    end=payload.end,
                )

            if capability == "calendar.read" and action == "schedule":
                return execute_google_calendar_scheduling(
                    account=account,
                    credential_resolution=credential_result,
                    search_start=payload.search_start or payload.start,
                    search_end=payload.search_end or payload.end,
                    duration_minutes=payload.duration_minutes,
                    max_results=payload.max_results,
                )

            if capability == "calendar.read" and action == "free_busy":
                return execute_google_calendar_free_busy(
                    account=account,
                    credential_resolution=credential_result,
                    start=payload.start,
                    end=payload.end,
                )

            if capability == "calendar.write" and action in {
                "create",
                "update",
                "delete",
            }:
                natural_start = self._natural_language_calendar_start(
                    payload.message,
                    payload.start,
                )
                result = execute_google_calendar_write(
                    account=account,
                    credential_resolution=credential_result,
                    action=action,
                    event_id=payload.event_id,
                    summary=payload.summary,
                    start=natural_start,
                    end=payload.end,
                    description=payload.description,
                    location=payload.location,
                    confirmed=payload.confirmed,
                    recurrence=payload.recurrence,
                )
                result["_natural_language_datetime"] = {
                    "status": "resolved" if natural_start else "not_used",
                    "start": natural_start,
                    "timezone": "Asia/Ho_Chi_Minh" if natural_start else None,
                }
                return result

            return {
                "status": "unsupported_action",
                "action": action,
                "provider_called": False,
            }
        except ValueError as exc:
            if str(exc).startswith("provider_called_must_"):
                raise
            return {
                "status": "validation_error",
                "error": str(exc),
                "provider_called": False,
            }
        except Exception as exc:
            return {
                "status": "provider_error",
                "error": str(exc),
                "provider_called": True,
            }


calendar_handler = CalendarHandler()
