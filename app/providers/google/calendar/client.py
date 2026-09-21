from __future__ import annotations

from typing import Any, Protocol

from app.providers.google.calendar.adapter import GoogleCalendarAdapter


CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_WRITE_SCOPE = "https://www.googleapis.com/auth/calendar"


class GoogleCredentialContext(Protocol):
    """Short-lived credential context supplied by CredentialResolver."""

    credentials: Any


def build_calendar_service(credential_context: GoogleCredentialContext) -> Any:
    """Build the Google Calendar API service from an authorized credential.

    Credential resolution/storage is intentionally outside this module.
    The Google SDK is imported lazily so the provider boundary stays optional
    until the Google Calendar capability is enabled.
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
    """Create the Calendar provider adapter after authorization/credential resolution."""
    return GoogleCalendarAdapter(build_calendar_service(credential_context))
