from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.security import new_request_id


def _request_id(request: Request) -> str:
    value = getattr(request.state, "request_id", None)
    if value:
        return value
    header = request.headers.get("X-Request-Id")
    return header or new_request_id()


def _safe_message(detail: Any, status_code: int) -> str:
    if isinstance(detail, str):
        return detail
    if status_code == 422:
        return "Dữ liệu request không hợp lệ."
    return "Yêu cầu không thể được xử lý."


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status = exc.status_code
    code_by_status = {
        400: "BAD_REQUEST",
        401: "SERVER_AUTHENTICATION_FAILED",
        403: "AUTHORIZATION_DENIED",
        404: "RESOURCE_NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        502: "UPSTREAM_ERROR",
        503: "SERVICE_UNAVAILABLE",
        504: "UPSTREAM_TIMEOUT",
    }
    code = code_by_status.get(status, "INTERNAL_ERROR")
    return JSONResponse(
        status_code=status,
        content={
            "status": "error",
            "error": {
                "code": code,
                "message": _safe_message(exc.detail, status),
            },
            "request_id": _request_id(request),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dữ liệu request không hợp lệ.",
            },
            "request_id": _request_id(request),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Không trả exception detail để tránh lộ secret, filesystem path hoặc nội bộ server.
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Đã xảy ra lỗi nội bộ.",
            },
            "request_id": _request_id(request),
        },
    )
