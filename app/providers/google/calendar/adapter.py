from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class GoogleCalendarService(Protocol):
    """Giao diện tối thiểu mà Google Calendar service phải cung cấp."""

    def events(self) -> Any: ...

    def freebusy(self) -> Any: ...


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    calendar_id: str
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: dict[str, Any] | None = None
    end: dict[str, Any] | None = None
    status: str | None = None
    html_link: str | None = None
    attendees: list[dict[str, Any]] | None = None
    recurrence: list[str] | None = None
    raw: dict[str, Any] | None = None


class GoogleCalendarAdapter:
    """Adapter Google Calendar cho thao tác CRUD event.

    Lớp này chỉ chuyển đổi request/response của provider. Authorization,
    chọn account và phân giải credential phải hoàn tất trước khi gọi lớp này.
    """

    provider = "google"

    def __init__(self, service: GoogleCalendarService) -> None:
        self._service = service

    def list_events(
        self,
        *,
        calendar_id: str,
        time_min: str | None = None,
        time_max: str | None = None,
        query: str | None = None,
        max_results: int | None = None,
    ) -> list[CalendarEvent]:
        params: dict[str, Any] = {"calendarId": calendar_id}
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if query:
            params["q"] = query
        if max_results:
            params["maxResults"] = max_results

        response = self._service.events().list(**params).execute()
        return [self._map_event(calendar_id, item) for item in response.get("items", [])]

    def get_event(self, *, calendar_id: str, event_id: str) -> CalendarEvent:
        response = (
            self._service.events()
            .get(calendarId=calendar_id, eventId=event_id)
            .execute()
        )
        return self._map_event(calendar_id, response)

    def create_event(self, *, calendar_id: str, event: dict[str, Any]) -> CalendarEvent:
        response = (
            self._service.events()
            .insert(calendarId=calendar_id, body=event)
            .execute()
        )
        return self._map_event(calendar_id, response)

    def update_event(
        self,
        *,
        calendar_id: str,
        event_id: str,
        event: dict[str, Any],
    ) -> CalendarEvent:
        response = (
            self._service.events()
            .patch(calendarId=calendar_id, eventId=event_id, body=event)
            .execute()
        )
        return self._map_event(calendar_id, response)

    def delete_event(self, *, calendar_id: str, event_id: str) -> None:
        (
            self._service.events()
            .delete(calendarId=calendar_id, eventId=event_id)
            .execute()
        )

    def free_busy(
        self,
        *,
        time_min: str,
        time_max: str,
        calendar_ids: list[str],
        time_zone: str | None = None,
    ) -> dict[str, list[dict[str, str]]]:
        body: dict[str, Any] = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id} for calendar_id in calendar_ids],
        }
        if time_zone:
            body["timeZone"] = time_zone
        response = self._service.freebusy().query(body=body).execute()
        calendars = response.get("calendars", {})
        return {
            str(calendar_id): [
                {"start": str(period["start"]), "end": str(period["end"])}
                for period in calendar_data.get("busy", [])
            ]
            for calendar_id, calendar_data in calendars.items()
        }

    @staticmethod
    def _map_event(calendar_id: str, raw: dict[str, Any]) -> CalendarEvent:
        return CalendarEvent(
            id=str(raw["id"]),
            calendar_id=calendar_id,
            summary=raw.get("summary"),
            description=raw.get("description"),
            location=raw.get("location"),
            start=raw.get("start"),
            end=raw.get("end"),
            status=raw.get("status"),
            html_link=raw.get("htmlLink"),
            attendees=raw.get("attendees"),
            recurrence=raw.get("recurrence"),
            raw=raw,
        )
