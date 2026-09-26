from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_is_available():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_has_security_headers():
    response = TestClient(app).get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_api_cors_is_not_wildcard():
    response = TestClient(app).options(
        "/api/v1/agent/chat",
        headers={
            "Origin": "http://127.0.0.1:8001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,x-request-id,x-user-id,x-organization-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8001"
    assert response.headers["access-control-allow-credentials"] == "false"
