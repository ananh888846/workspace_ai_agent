import pytest

from app.application.execution_boundary import build_boundary_error


@pytest.mark.parametrize(
    "code",
    [
        "account_not_found",
        "account_selection_required",
        "authorization_denied",
        "oauth_required",
        "validation_error",
        "confirmation_required",
        "unsupported_action",
    ],
)
def test_pre_provider_errors_never_mark_provider_called(code: str) -> None:
    result = build_boundary_error(code=code, message="blocked", action="calendar")

    assert result["status"] == code
    assert result["provider_called"] is False
    assert result["error"]["provider_called"] is False
    assert result["error"]["retryable"] is False


def test_provider_error_requires_provider_boundary() -> None:
    result = build_boundary_error(
        code="provider_error",
        message="Google Calendar timeout",
        action="list_events",
        retryable=True,
        provider_called=True,
        details={"provider": "google", "kind": "timeout"},
    )

    assert result["status"] == "provider_error"
    assert result["provider_called"] is True
    assert result["error"]["provider_called"] is True
    assert result["error"]["retryable"] is True


def test_provider_error_without_provider_call_is_rejected() -> None:
    with pytest.raises(ValueError, match="provider_called_must_be_true"):
        build_boundary_error(
            code="provider_error",
            message="provider failed before call marker",
            action="list_events",
            provider_called=False,
        )


def test_pre_provider_error_with_provider_called_is_rejected() -> None:
    with pytest.raises(ValueError, match="provider_called_must_be_false"):
        build_boundary_error(
            code="authorization_denied",
            message="not allowed",
            action="delete_event",
            provider_called=True,
        )


def test_pre_provider_error_cannot_be_marked_retryable() -> None:
    with pytest.raises(ValueError, match="retryable_must_be_false"):
        build_boundary_error(
            code="confirmation_required",
            message="confirmation needed",
            action="delete_event",
            retryable=True,
        )
