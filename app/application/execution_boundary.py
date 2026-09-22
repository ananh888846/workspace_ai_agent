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
    """Tạo Error/Result Contract và enforce provider boundary V1."""
    normalized_code = normalize_result_status(code)

    if normalized_code in PRE_PROVIDER_ERROR_CODES:
        if provider_called:
            raise ValueError(f"provider_called_must_be_false_for_{normalized_code}")
        if retryable:
            raise ValueError(f"retryable_must_be_false_for_{normalized_code}")

    if normalized_code == ExecutionStatus.PROVIDER_ERROR.value and not provider_called:
        raise ValueError("provider_called_must_be_true_for_provider_error")

    return build_error_result(
        code=normalized_code,
        message=message,
        action=action,
        retryable=retryable,
        provider_called=provider_called,
        details=details,
    ).copy()


def enforce_result_boundary(result: dict) -> dict:
    """Kiểm tra result capability sau Tool/Provider và trả về bản chuẩn hóa.

    Đây là điểm chặn cuối của Application layer: mọi capability result đi qua
    đây trước khi được đưa vào API response. Hàm không tự suy đoán provider đã
    gọi; nó kiểm tra fact ``provider_called`` do tầng thực thi cung cấp.
    """
    normalized = dict(result)
    status = normalize_result_status(str(normalized.get("status", "")))
    provider_called = bool(normalized.get("provider_called", False))
    error = normalized.get("error")

    normalized["status"] = status
    normalized["provider_called"] = provider_called

    if status in PRE_PROVIDER_ERROR_CODES and provider_called:
        raise ValueError(f"provider_called_must_be_false_for_{status}")

    if status == ExecutionStatus.PROVIDER_ERROR.value and not provider_called:
        raise ValueError("provider_called_must_be_true_for_provider_error")

    if isinstance(error, dict):
        normalized_error = dict(error)
        normalized_error["code"] = normalize_result_status(str(normalized_error.get("code", status)))
        normalized_error["provider_called"] = provider_called
        normalized["error"] = normalized_error

    return normalized
