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

 
def test_account_resolver_single_candidate_returns_resolved_account():
    from app.application.core_runtime import AccountCandidate, AccountResolver, ExternalAccount, ResolvedAccount

    account = ExternalAccount(
        id="a1", user_id="user-1", provider="google", account_type="oauth",
        external_account_id="google-a1", status="active",
    )

    class Repo:
        def find_candidates(self, **kwargs):
            return [AccountCandidate(account=account, access_mode="owner", organization_id="org-1")]

    resolved = AccountResolver(Repo()).resolve(
        user_id="user-1", organization_id="org-1", provider="google"
    )
    assert isinstance(resolved, ResolvedAccount)
    assert resolved.access_mode == "owner"
    assert resolved.account.id == "a1"


def test_account_resolver_multiple_candidates_requires_selection():
    from app.application.core_runtime import AccountCandidate, AccountResolver, AccountSelectionRequiredError, ExternalAccount

    def make_account(account_id):
        return ExternalAccount(
            id=account_id, user_id="user-1", provider="google", account_type="oauth",
            external_account_id=account_id, status="active",
        )

    class Repo:
        def find_candidates(self, **kwargs):
            return [
                AccountCandidate(account=make_account("a1"), access_mode="owner"),
                AccountCandidate(account=make_account("a2"), access_mode="owner"),
            ]

    try:
        AccountResolver(Repo()).resolve(
            user_id="user-1", organization_id="org-1", provider="google"
        )
    except AccountSelectionRequiredError as exc:
        assert str(exc) == "account_selection_required"
    else:
        raise AssertionError("expected account_selection_required")


def test_grantee_scope_is_forwarded_to_account_authorization():
    from app.application.core_runtime import AgentContext, AuthorizationService, ExternalAccount, ResolvedAccount

    class Permissions:
        def __init__(self):
            self.calls = []

        def has_capability_permission(self, **kwargs):
            return True

        def has_account_access(self, **kwargs):
            self.calls.append(kwargs)
            return True

        def has_resource_access(self, **kwargs):
            return True

    permissions = Permissions()
    resolved = ResolvedAccount(
        account=ExternalAccount(
            id="shared", user_id="owner-1", provider="google", account_type="oauth",
            external_account_id="google-shared", status="active",
        ),
        access_mode="grant",
        account_grant_id="grant-1",
        organization_id="org-1",
        grant_scope={"capabilities": ["calendar.read"]},
    )
    decision = AuthorizationService(permissions).authorize(
        context=AgentContext(
            request_id="req-1", organization_id="org-1", user_id="user-1",
            capability="calendar.read", action="read",
        ),
        account=resolved.account,
        resolved_account=resolved,
    )

    assert decision.allowed is True
    assert permissions.calls[0]["access_mode"] == "grant"
    assert permissions.calls[0]["grant_scope"] == {"capabilities": ["calendar.read"]}
