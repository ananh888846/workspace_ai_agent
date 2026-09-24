from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.config.settings import get_settings
from app.api.security import require_agent_server_context


def _call(*, token: str | None, request_id: str = "123e4567-e89b-12d3-a456-426614174000"):
    return require_agent_server_context(
        authorization=f"Bearer {token}" if token is not None else None,
        x_request_id=request_id,
        x_user_id="user-100",
        x_organization_id="org-10",
    )


def test_server_token_allows_context(monkeypatch):
    monkeypatch.setattr("app.api.security.get_settings", lambda: type("S", (), {"agent_server_token": "test-secret"})())

    result = _call(token="test-secret")

    assert result["user_id"] == "user-100"
    assert result["organization_id"] == "org-10"
    assert result["request_id"] == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.parametrize(
    "authorization",
    [None, "Bearer wrong-secret", "Basic test-secret", "Bearer "],
)
def test_invalid_server_auth_is_401(monkeypatch, authorization):
    monkeypatch.setattr("app.api.security.get_settings", lambda: type("S", (), {"agent_server_token": "test-secret"})())

    with pytest.raises(HTTPException) as exc:
        require_agent_server_context(
            authorization=authorization,
            x_request_id="123e4567-e89b-12d3-a456-426614174000",
            x_user_id="user-100",
            x_organization_id="org-10",
        )

    assert exc.value.status_code == 401


def test_missing_request_id_is_400(monkeypatch):
    monkeypatch.setenv("AGENT_SERVER_TOKEN", "test-secret")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc:
        require_agent_server_context(
            authorization="Bearer test-secret",
            x_request_id=None,
            x_user_id="user-100",
            x_organization_id="org-10",
        )

    assert exc.value.status_code == 400


def test_identity_headers_are_required_after_authentication(monkeypatch):
    monkeypatch.setenv("AGENT_SERVER_TOKEN", "test-secret")
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as exc:
        require_agent_server_context(
            authorization="Bearer test-secret",
            x_request_id="123e4567-e89b-12d3-a456-426614174000",
            x_user_id=None,
            x_organization_id="org-10",
        )

    assert exc.value.status_code == 400
