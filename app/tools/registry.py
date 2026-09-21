from __future__ import annotations

from app.providers.google.calendar.client import build_calendar_adapter
from app.tools.calendar import GoogleCalendarTool


class CalendarToolRegistry:
    """Đăng ký và phân giải tool Calendar theo capability, provider và action."""

    def __init__(self) -> None:
        self._google_calendar = GoogleCalendarTool(build_calendar_adapter)

    def resolve(self, *, capability: str, provider: str, action: str) -> GoogleCalendarTool:
        if provider != "google":
            raise LookupError("calendar_provider_not_supported")
        if capability not in {"calendar.read", "calendar.write"}:
            raise LookupError("calendar_capability_not_supported")
        if action not in {
            "list_events",
            "get_event",
            "create_event",
            "update_event",
            "delete_event",
        }:
            raise LookupError("calendar_action_not_supported")
        return self._google_calendar
