from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ExecutionStatus(StrEnum):
    """Các trạng thái chuẩn của Agent Execution."""

    NOT_CLASSIFIED = "not_classified"
    ACCOUNT_NOT_FOUND = "account_not_found"
    ACCOUNT_SELECTION_REQUIRED = "account_selection_required"
    AUTHORIZATION_DENIED = "authorization_denied"
    OAUTH_REQUIRED = "oauth_required"
    VALIDATION_ERROR = "validation_error"
    CONFIRMATION_REQUIRED = "confirmation_required"
    PROVIDER_ERROR = "provider_error"
    UNSUPPORTED_ACTION = "unsupported_action"
    OK = "ok"


@dataclass(frozen=True)
class ExecutionContract:
    """Contract chuẩn mô tả đường đi của một Agent Run."""

    intent: str
    capability: str | None
    action: str | None
    account: dict[str, Any] = field(default_factory=lambda: {"status": "not_evaluated"})
    authorization: dict[str, Any] = field(default_factory=lambda: {"status": "not_evaluated"})
    credential: dict[str, Any] = field(default_factory=lambda: {"status": "not_evaluated"})
    provider_called: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển execution contract sang JSON-compatible dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class ErrorContract:
    """Contract lỗi ổn định giữa Application, Graph, Tool và API."""

    code: str
    message: str
    retryable: bool = False
    provider_called: bool = False
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Chuyển error contract sang dictionary để trả API hoặc ghi audit."""
        return asdict(self)


@dataclass(frozen=True)
class ResultContract:
    """Contract chuẩn cho kết quả capability."""

    status: str
    action: str | None = None
    data: Any = None
    error: ErrorContract | None = None
    provider_called: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển result contract sang dictionary."""
        result = asdict(self)
        if self.error is not None:
            result["error"] = self.error.to_dict()
        return result


def build_execution_contract(
    *,
    intent: str,
    capability: str | None,
    action: str | None,
    account: dict[str, Any] | None = None,
    authorization: dict[str, Any] | None = None,
    credential: dict[str, Any] | None = None,
    provider_called: bool = False,
) -> dict[str, Any]:
    """Tạo execution contract thống nhất cho mọi capability."""
    return ExecutionContract(
        intent=intent,
        capability=capability,
        action=action,
        account=account or {"status": "not_evaluated"},
        authorization=authorization or {"status": "not_evaluated"},
        credential=credential or {"status": "not_evaluated"},
        provider_called=provider_called,
    ).to_dict()


def build_error_result(
    *,
    code: str,
    message: str,
    action: str | None = None,
    retryable: bool = False,
    provider_called: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tạo result lỗi chuẩn và không gọi provider nếu chưa được phép."""
    return ResultContract(
        status=code,
        action=action,
        error=ErrorContract(
            code=code,
            message=message,
            retryable=retryable,
            provider_called=provider_called,
            details=details,
        ),
        provider_called=provider_called,
    ).to_dict()


def normalize_result_status(status: str) -> str:
    """Chuẩn hóa các trạng thái runtime về nhóm status của Execution Contract."""
    aliases = {
        "not_found": ExecutionStatus.ACCOUNT_NOT_FOUND.value,
        "account_not_found": ExecutionStatus.ACCOUNT_NOT_FOUND.value,
        "account_selection_required": ExecutionStatus.ACCOUNT_SELECTION_REQUIRED.value,
        "deny": ExecutionStatus.AUTHORIZATION_DENIED.value,
        "oauth_required": ExecutionStatus.OAUTH_REQUIRED.value,
        "validation_error": ExecutionStatus.VALIDATION_ERROR.value,
        "confirmation_required": ExecutionStatus.CONFIRMATION_REQUIRED.value,
        "provider_error": ExecutionStatus.PROVIDER_ERROR.value,
        "unsupported_action": ExecutionStatus.UNSUPPORTED_ACTION.value,
        "ok": ExecutionStatus.OK.value,
    }
    return aliases.get(status, status)
