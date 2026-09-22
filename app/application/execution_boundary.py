from __future__ import annotations

from app.application.execution_contract import (
    ExecutionStatus,
    build_error_result,
    normalize_result_status,
)


PRE_PROVIDER_ERROR_CODES = frozenset(
    {
        ExecutionStatus.ACCOUNT_NOT_FOUND.value,
        ExecutionStatus.ACCOUNT_SELECTION_REQUIRED.value,
        ExecutionStatus.AUTHORIZATION_DENIED.value,
        ExecutionStatus.OAUTH_REQUIRED.value,
        ExecutionStatus.VALIDATION_ERROR.value,
        ExecutionStatus.CONFIRMATION_REQUIRED.value,
        ExecutionStatus.UNSUPPORTED_ACTION.value,
    }
)


def build_boundary_error(
    *,
    code: str,
    message: str,
    action: str | None = None,
    retryable: bool = False,
    provider_called: bool = False,
    details: dict | None = None,
) -> dict:
    """Tạo Error/Result Contract và enforce provider boundary V1.

    Các lỗi trước provider không được phép mang ``provider_called=true``.
    Chỉ ``provider_error`` mới có thể biểu diễn lỗi sau khi provider đã được gọi.
    Retry chỉ được bật mặc định cho lỗi provider.
    """
    normalized_code = normalize_result_status(code)

    if normalized_code in PRE_PROVIDER_ERROR_CODES:
        if provider_called:
            raise ValueError(
                f"provider_called_must_be_false_for_{normalized_code}"
            )
        if retryable:
            raise ValueError(
                f"retryable_must_be_false_for_{normalized_code}"
            )

    if normalized_code == ExecutionStatus.PROVIDER_ERROR.value and not provider_called:
        raise ValueError("provider_called_must_be_true_for_provider_error")

    return build_error_result(
        code=normalized_code,
        message=message,
        action=action,
        retryable=retryable,
        provider_called=provider_called,
        details=details,
    )
