from __future__ import annotations

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import psycopg
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.chat import authorize_request, build_chat_response, classify_chat_request, resolve_google_account
from app.api.schemas import ChatRequest
from app.application.core_runtime import ExternalAccount
from app.application.capabilities.calendar import CalendarHandler, calendar_handler
from app.application.capabilities.knowledge import knowledge_handler
from app.agent_runtime.runtime import AgentRuntime, AgentRuntimeDependencies
from app.infrastructure.oauth.google import GoogleOAuthService
from app.config.settings import get_settings
from app.api.errors import http_exception_handler, unhandled_exception_handler, validation_exception_handler
from app.api.security import require_agent_server_context

settings = get_settings()
app = FastAPI(title="Workspace AI Agent", version="2.1-phase3")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(settings.app_allowed_hosts),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.app_cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-User-Id", "X-Organization-Id", "Idempotency-Key"],
    expose_headers=["X-Request-Id"],
)
if settings.app_enforce_https:
    app.add_middleware(HTTPSRedirectMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    account_hint: str | None = None
    capability: str | None = None
    action: str | None = None
    target_resource: str | None = None
    event_id: str | None = None
    summary: str | None = None
    start: str | None = None
    end: str | None = None
    description: str | None = None
    location: str | None = None
    confirmed: bool = False
    search_start: str | None = None
    search_end: str | None = None
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    max_results: int = Field(default=5, ge=1, le=20)
    recurrence: str | None = None


@app.get("/auth/google/start")
def google_oauth_start(
    account_id: str,
    capability: str = "calendar.read",
    server_context: dict[str, str] = Depends(require_agent_server_context),
) -> RedirectResponse:
    x_user_id = server_context["user_id"]
    x_organization_id = server_context["organization_id"]
    if capability not in {"calendar.read", "calendar.write"}:
        raise HTTPException(status_code=400, detail="unsupported_calendar_capability")
    account = resolve_google_account(
        user_id=x_user_id,
        organization_id=x_organization_id,
        account_hint=account_id,
    )
    if account.get("status") != "resolved":
        raise HTTPException(status_code=404, detail=account.get("status", "account_not_found"))
    external_account = ExternalAccount(
        id=account["account_id"],
        user_id=x_user_id,
        provider=account["provider"],
        account_type="oauth",
        external_account_id=account["external_account_id"],
        display_name=account["display_name"],
        email=account["email"],
        status=account.get("account_state", "active"),
    )
    authorization = authorize_request(
        user_id=x_user_id,
        organization_id=x_organization_id,
        capability=capability,
        action="read" if capability == "calendar.read" else "write",
        account=external_account,
    )
    if authorization.get("status") != "allow":
        raise HTTPException(status_code=403, detail=authorization.get("reason", "authorization_denied"))
    scopes = (
        [get_settings().google_calendar_read_scope]
        if capability == "calendar.read"
        else [get_settings().google_calendar_write_scope]
    )
    try:
        url = GoogleOAuthService().authorization_url(
            account_id=account["account_id"],
            user_id=x_user_id,
            organization_id=x_organization_id,
            scopes=scopes,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=302)


@app.get("/auth/google/callback")
def google_oauth_callback(code: str, state: str) -> dict:
    try:
        oauth_state = GoogleOAuthService().handle_callback(code=code, state=state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "ok",
        "account_id": oauth_state.account_id,
        "organization_id": oauth_state.organization_id,
        "message": "Google OAuth hoàn tất.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/dependencies")
def health_dependencies() -> JSONResponse:
    """Kiểm tra local runtime dependencies mà không trả secret/config nội bộ."""
    checks: dict[str, dict[str, object]] = {}

    if settings.database_url:
        try:
            with psycopg.connect(settings.database_url, connect_timeout=2) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            checks["postgresql"] = {"status": "ok"}
        except Exception:
            checks["postgresql"] = {"status": "error"}
    else:
        checks["postgresql"] = {"status": "not_configured"}

    try:
        response = httpx.get(f"{settings.qdrant_url.rstrip('/')}/collections", timeout=2.0)
        response.raise_for_status()
        checks["qdrant"] = {"status": "ok"}
    except Exception:
        checks["qdrant"] = {"status": "error"}

    try:
        response = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=2.0)
        response.raise_for_status()
        payload = response.json()
        checks["ollama"] = {
            "status": "ok",
            "chat_model": settings.ollama_chat_model,
            "embedding_model": settings.ollama_embedding_model,
            "models_available": len(payload.get("models", [])) if isinstance(payload, dict) else 0,
        }
    except Exception:
        checks["ollama"] = {"status": "error"}

    required_ok = checks["postgresql"]["status"] == "ok" and checks["qdrant"]["status"] == "ok"
    all_ok = required_ok and checks["ollama"]["status"] == "ok"
    body = {
        "status": "ok" if all_ok else ("degraded" if required_ok else "error"),
        "checks": checks,
    }
    return JSONResponse(status_code=200 if required_ok else 503, content=body)


def _classify_agent_request(payload: AgentChatRequest) -> tuple[str, str | None, str | None]:
    request = ChatRequest(
        message=payload.message,
        conversation_id=payload.conversation_id,
        account_hint=payload.account_hint,
        capability=payload.capability,
        action=payload.action,
        target_resource=payload.target_resource,
    )
    return classify_chat_request(request)


def _unsupported_handler(state: dict) -> dict:
    # Requests carrying an explicit account hint still use the account-resolution
    # boundary even when no capability was classified yet.
    payload = state.get("request")
    if payload is not None and getattr(payload, "account_hint", None):
        return calendar_handler.handle(state)

    from app.application.execution_contract import build_execution_contract

    response = build_chat_response(
        ChatRequest(
            message=payload.message if payload is not None else "",
            conversation_id=payload.conversation_id if payload is not None else None,
        )
    )
    return {
        "status": "unsupported_action",
        "conversation_id": response.conversation_id,
        "message": "Capability chưa được hỗ trợ bởi runtime hiện tại.",
        "execution": build_execution_contract(
            intent=state.get("intent", "not_classified"),
            capability=state.get("capability"),
            action=state.get("action"),
            provider_called=False,
        ),
        "provider_called": False,
    }


_agent_runtime = AgentRuntime(
    AgentRuntimeDependencies(
        classify=_classify_agent_request,
        route_handlers={
            "calendar.read": calendar_handler.handle,
            "calendar.write": calendar_handler.handle,
            "knowledge.read": knowledge_handler.handle,
            "default": _unsupported_handler,
        },
    )
)


@app.post("/api/v1/agent/chat")
def agent_chat(
    server_context: dict[str, str] = Depends(require_agent_server_context),
    payload: AgentChatRequest = Body(...),
) -> dict:
    context = {
        "request_id": server_context["request_id"],
        "user_id": server_context["user_id"],
        "organization_id": server_context["organization_id"],
    }
    result = _agent_runtime.run(request=payload, context=context)
    result["request_id"] = server_context["request_id"]
    return result


# Backward-compatible endpoint for the Laravel V1 client.
# Canonical API remains /api/v1/agent/chat.
@app.post("/api/agent/chat")
def agent_chat_legacy(
    server_context: dict[str, str] = Depends(require_agent_server_context),
    payload: AgentChatRequest = Body(...),
) -> dict:
    return agent_chat(payload=payload, server_context=server_context)


# Compatibility helper: các test/API nội bộ cũ vẫn có thể import helper từ app.main.
_natural_language_calendar_start = CalendarHandler._natural_language_calendar_start
