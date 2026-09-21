from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.providers.google.calendar.adapter import GoogleCalendarAdapter


CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_WRITE_SCOPE = "https://www.googleapis.com/auth/calendar"


@dataclass(frozen=True)
class GoogleCredentialContext:
    """Ngữ cảnh credential ngắn hạn do CredentialResolver cấp."""

    credentials: Any


def build_calendar_service(credential_context: GoogleCredentialContext) -> Any:
    """Build the Google Calendar API service from an authorized credential.

    Phân giải và lưu credential nằm ngoài module này.
    Google SDK được import trễ để provider chỉ được tải khi Calendar được gọi.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Calendar runtime requires google-api-python-client."
        ) from exc

    return build(
        "calendar",
        "v3",
        credentials=credential_context.credentials,
        cache_discovery=False,
    )


def build_calendar_adapter(credential_context: GoogleCredentialContext) -> GoogleCalendarAdapter:
    """Tạo adapter Calendar sau khi đã Authorization và CredentialResolver."""
    return GoogleCalendarAdapter(build_calendar_service(credential_context))
