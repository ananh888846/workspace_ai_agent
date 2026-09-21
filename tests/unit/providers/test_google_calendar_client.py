from app.providers.google.calendar.client import (
    CALENDAR_READONLY_SCOPE,
    CALENDAR_WRITE_SCOPE,
)


def test_calendar_scopes_are_provider_constants():
    assert CALENDAR_READONLY_SCOPE.endswith("/calendar.readonly")
    assert CALENDAR_WRITE_SCOPE.endswith("/calendar")
    assert CALENDAR_READONLY_SCOPE != CALENDAR_WRITE_SCOPE
