from app.application.execution_contract import (
    ExecutionStatus,
    build_error_result,
    build_execution_contract,
    normalize_result_status,
)


def test_execution_contract_has_stable_runtime_shape() -> None:
    result = build_execution_contract(
        intent="calendar",
        capability="calendar.read",
        action="read",
    )

    assert result == {
        "intent": "calendar",
        "capability": "calendar.read",
        "action": "read",
        "account": {"status": "not_evaluated"},
        "authorization": {"status": "not_evaluated"},
        "credential": {"status": "not_evaluated"},
        "provider_called": False,
    }


def test_error_result_contains_machine_code_and_provider_boundary() -> None:
    result = build_error_result(
        code=ExecutionStatus.CONFIRMATION_REQUIRED.value,
        message="Cần xác nhận trước khi xóa sự kiện.",
        action="delete_event",
    )

    assert result["status"] == "confirmation_required"
    assert result["action"] == "delete_event"
    assert result["provider_called"] is False
    assert result["error"] == {
        "code": "confirmation_required",
        "message": "Cần xác nhận trước khi xóa sự kiện.",
        "retryable": False,
        "provider_called": False,
        "details": None,
    }


def test_provider_error_can_be_marked_retryable() -> None:
    result = build_error_result(
        code="provider_error",
        message="Google Calendar tạm thời không phản hồi.",
        action="list_events",
        retryable=True,
        provider_called=True,
        details={"provider": "google"},
    )

    assert result["status"] == "provider_error"
    assert result["provider_called"] is True
    assert result["error"]["retryable"] is True
    assert result["error"]["provider_called"] is True
    assert result["error"]["details"] == {"provider": "google"}


def test_runtime_status_aliases_are_normalized() -> None:
    assert normalize_result_status("not_found") == "account_not_found"
    assert normalize_result_status("deny") == "authorization_denied"
    assert normalize_result_status("ok") == "ok"
