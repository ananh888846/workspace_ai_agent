from __future__ import annotations

import hmac
from uuid import UUID, uuid4

from fastapi import Header, HTTPException

from app.config.settings import get_settings


def require_agent_server_context(
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_organization_id: str | None = Header(default=None),
) -> dict[str, str]:
    """Xác thực Laravel trước khi tạo execution context.

    Identity headers chỉ được chấp nhận sau khi server-to-server token hợp lệ.
    Không log token và không đưa token vào AgentContext.
    """
    settings = get_settings()
    expected = settings.agent_server_token
    if not expected:
        raise HTTPException(status_code=503, detail="agent_server_auth_not_configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="server_authentication_required")

    supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="server_authentication_failed")

    request_id = (x_request_id or "").strip()
    if not request_id:
        raise HTTPException(status_code=400, detail="x_request_id_required")
    try:
        UUID(request_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="x_request_id_must_be_uuid") from exc

    user_id = (x_user_id or "").strip()
    organization_id = (x_organization_id or "").strip()
    if not user_id or not organization_id:
        raise HTTPException(status_code=400, detail="x_user_id_and_x_organization_id_required")

    return {
        "request_id": request_id,
        "user_id": user_id,
        "organization_id": organization_id,
    }


def new_request_id() -> str:
    """Tạo request ID an toàn cho error xảy ra trước khi dependency hoàn tất."""
    return str(uuid4())
