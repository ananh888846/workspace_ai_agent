from __future__ import annotations

from typing import Any, Callable

from app.providers.google.calendar.adapter import CalendarEvent, GoogleCalendarAdapter


class GoogleCalendarTool:
    """Thin tool layer around the Google Calendar provider adapter.

    Authorization and credential resolution happen in the application layer.
    This tool receives an already-authorized credential context.
    """

    provider = "google"

    def __init__(self, adapter_factory: Callable[[Any], GoogleCalendarAdapter]) -> None:
        self._adapter_factory = adapter_factory

    def execute(self, action: str, *, credential_context: Any, **kwargs: Any) -> Any:
        adapter = self._adapter_factory(credential_context)

        handlers = {
            "list_events": self.list_events,
            "get_event": self.get_event,
            "create_event": self.create_event,
            "update_event": self.update_event,
            "delete_event": self.delete_event,
            "free_busy": self.free_busy,
        }
        handler = handlers.get(action)
        if handler is None:
            raise ValueError(f"Unsupported calendar action: {action}")
        return handler(adapter=adapter, **kwargs)

    @staticmethod
    def list_events(
        *, adapter: GoogleCalendarAdapter, calendar_id: str, **kwargs: Any
    ) -> list[CalendarEvent]:
        return adapter.list_events(calendar_id=calendar_id, **kwargs)

    @staticmethod
    def get_event(
        *, adapter: GoogleCalendarAdapter, calendar_id: str, event_id: str
    ) -> CalendarEvent:
        return adapter.get_event(calendar_id=calendar_id, event_id=event_id)

    @staticmethod
    def create_event(
        *, adapter: GoogleCalendarAdapter, calendar_id: str, event: dict[str, Any]
    ) -> CalendarEvent:
        return adapter.create_event(calendar_id=calendar_id, event=event)

    @staticmethod
    def update_event(
        *,
        adapter: GoogleCalendarAdapter,
        calendar_id: str,
        event_id: str,
        event: dict[str, Any],
    ) -> CalendarEvent:
        if not event_id:
            raise ValueError("event_id is required for update")
        return adapter.update_event(
            calendar_id=calendar_id,
            event_id=event_id,
            event=event,
        )

    @staticmethod
    def delete_event(
        *, adapter: GoogleCalendarAdapter, calendar_id: str, event_id: str
    ) -> None:
        if not event_id:
            raise ValueError("event_id is required for delete")
        adapter.delete_event(calendar_id=calendar_id, event_id=event_id)


    @staticmethod
    def free_busy(
        *,
        adapter: GoogleCalendarAdapter,
        calendar_ids: list[str],
        time_min: str,
        time_max: str,
        time_zone: str | None = None,
    ) -> dict[str, list[dict[str, str]]]:
        return adapter.free_busy(
            calendar_ids=calendar_ids,
            time_min=time_min,
            time_max=time_max,
            time_zone=time_zone,
        )
