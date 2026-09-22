from __future__ import annotations

import os
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.main import app


VN = ZoneInfo("Asia/Ho_Chi_Minh")


def _e2e_enabled() -> bool:
    return os.getenv("RUN_GOOGLE_CALENDAR_E2E", "").strip() == "1"


pytestmark = pytest.mark.skipif(
    not _e2e_enabled(),
    reason=(
        "Google Calendar E2E cần RUN_GOOGLE_CALENDAR_E2E=1; "
        "không chạy trong regression mặc định."
    ),
)


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        pytest.fail(f"Thiếu biến môi trường E2E: {name}")
    return value


def _headers() -> dict[str, str]:
    return {
        "X-User-ID": _required_env("WORKSPACE_E2E_USER_ID"),
        "X-Organization-ID": _required_env("WORKSPACE_E2E_ORGANIZATION_ID"),
    }


def _account_hint() -> str | None:
    return os.getenv("WORKSPACE_E2E_ACCOUNT_HINT") or None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def e2e_event(client: TestClient):
    """Tạo event thật qua Agent Runtime và dọn event sau test."""
    now = datetime.now(VN)
    start = (now + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(hours=1)
    summary = f"Workspace AI Agent E2E {uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(),
        json={
            "message": f"Tạo cuộc họp {summary} ngày kiểm thử.",
            "conversation_id": f"e2e-create-{uuid4()}",
            "account_hint": _account_hint(),
            "summary": summary,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["execution"]["intent"] == "calendar"
    assert body["execution"]["capability"] == "calendar.write"
    assert body["execution"]["action"] == "create"
    assert body["calendar"]["status"] == "ok", body
    assert body["calendar"]["provider_called"] is True

    event_id = body["calendar"]["event"]["id"]
    assert event_id

    state = {
        "event_id": event_id,
        "summary": summary,
        "start": start,
        "end": end,
    }
    yield state

    if state["event_id"] is None:
        return

    cleanup = client.post(
        "/api/v1/agent/chat",
        headers=_headers(),
        json={
            "message": f"Xóa cuộc hẹn {summary}",
            "conversation_id": f"e2e-cleanup-{uuid4()}",
            "account_hint": _account_hint(),
            "event_id": state["event_id"],
            "confirmed": True,
        },
    )
    assert cleanup.status_code == 200, cleanup.text
    cleanup_body = cleanup.json()
    assert cleanup_body["calendar"]["status"] == "ok", cleanup_body


def test_real_google_calendar_create_and_read(client: TestClient, e2e_event) -> None:
    """Kiểm tra Agent Runtime → CalendarHandler → Google Calendar bằng event thật."""
    response = client.post(
        "/api/v1/agent/chat",
        headers=_headers(),
        json={
            "message": "Đọc lịch",
            "conversation_id": f"e2e-read-{uuid4()}",
            "account_hint": _account_hint(),
            "start": e2e_event["start"].isoformat(),
            "end": e2e_event["end"].isoformat(),
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["execution"]["intent"] == "calendar"
    assert body["execution"]["capability"] == "calendar.read"
    assert body["execution"]["action"] == "read"
    assert body["calendar"]["status"] == "ok"
    assert body["calendar"]["provider_called"] is True

    matching = [
        event
        for event in body["calendar"]["events"]
        if event["id"] == e2e_event["event_id"]
    ]
    assert matching, body


def test_real_google_calendar_delete_requires_confirmation(
    client: TestClient, e2e_event
) -> None:
    """Delete chưa confirmation phải dừng trước Google Calendar provider."""
    first = client.post(
        "/api/v1/agent/chat",
        headers=_headers(),
        json={
            "message": f"Xóa cuộc hẹn {e2e_event['summary']}",
            "conversation_id": f"e2e-delete-confirm-{uuid4()}",
            "account_hint": _account_hint(),
            "event_id": e2e_event["event_id"],
            "confirmed": False,
        },
    )

    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["execution"]["capability"] == "calendar.write"
    assert first_body["execution"]["action"] == "delete"
    assert first_body["calendar"]["status"] == "confirmation_required"
    assert first_body["calendar"]["provider_called"] is False
    assert first_body["execution"]["provider_called"] is False

    second = client.post(
        "/api/v1/agent/chat",
        headers=_headers(),
        json={
            "message": f"Xóa cuộc hẹn {e2e_event['summary']}",
            "conversation_id": f"e2e-delete-confirmed-{uuid4()}",
            "account_hint": _account_hint(),
            "event_id": e2e_event["event_id"],
            "confirmed": True,
        },
    )

    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["calendar"]["status"] == "ok"
    assert second_body["calendar"]["provider_called"] is True
    assert second_body["execution"]["provider_called"] is True

    # Đã xóa thành công; fixture không được gọi cleanup lần nữa.
    e2e_event["event_id"] = None
