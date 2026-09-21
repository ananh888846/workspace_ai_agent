from app.providers.google.calendar.adapter import GoogleCalendarAdapter


class _Request:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _Events:
    def __init__(self):
        self.calls = []

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return _Request({"items": [{"id": "e1", "summary": "Demo"}]})

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return _Request({"id": "e1", "summary": "Demo"})

    def insert(self, **kwargs):
        self.calls.append(("insert", kwargs))
        return _Request({"id": "e2", "summary": kwargs["body"]["summary"]})

    def patch(self, **kwargs):
        self.calls.append(("patch", kwargs))
        return _Request({"id": kwargs["eventId"], "summary": kwargs["body"]["summary"]})

    def delete(self, **kwargs):
        self.calls.append(("delete", kwargs))
        return _Request({})


class _Service:
    def __init__(self):
        self.event_api = _Events()

    def events(self):
        return self.event_api


def test_calendar_crud_maps_to_google_events_api():
    service = _Service()
    adapter = GoogleCalendarAdapter(service)

    events = adapter.list_events(calendar_id="primary", query="demo")
    assert events[0].id == "e1"

    created = adapter.create_event(
        calendar_id="primary",
        event={"summary": "Created"},
    )
    assert created.id == "e2"

    updated = adapter.update_event(
        calendar_id="primary",
        event_id="e2",
        event={"summary": "Updated"},
    )
    assert updated.summary == "Updated"

    fetched = adapter.get_event(calendar_id="primary", event_id="e1")
    assert fetched.id == "e1"

    adapter.delete_event(calendar_id="primary", event_id="e1")

    names = [call[0] for call in service.event_api.calls]
    assert names == ["list", "insert", "patch", "get", "delete"]
