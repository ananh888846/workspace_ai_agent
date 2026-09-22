from datetime import datetime, timezone

from app.graphs.scheduling import SchedulingGraphDependencies, run_scheduling_graph
from app.services.calendar_free_busy import BusyPeriod


def dt(hour: int) -> datetime:
    return datetime(2026, 9, 24, hour, tzinfo=timezone.utc)


def test_scheduling_graph_orchestrates_nodes_and_service():
    calls = []

    def resolve_calendar(state):
        calls.append("resolve_calendar")
        return ["primary"]

    def get_free_busy(state, calendar_ids):
        calls.append(("get_free_busy", calendar_ids))
        return [BusyPeriod(calendar_id="primary", start=dt(10), end=dt(11))]

    result = run_scheduling_graph(
        search_start=dt(9),
        search_end=dt(13),
        duration_minutes=60,
        dependencies=SchedulingGraphDependencies(
            resolve_calendar=resolve_calendar,
            get_free_busy=get_free_busy,
        ),
    )

    assert calls == ["resolve_calendar", ("get_free_busy", ["primary"])]
    assert result["intent"] == "calendar"
    assert result["action"] == "schedule"
    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["status"] == "available"
    assert result["confirmation_state"] == "not_required"
    assert len(result["conflicts"]) == 1
    assert [(slot.start, slot.end) for slot in result["available_slots"]] == [
        (dt(9), dt(10)),
        (dt(11), dt(12)),
        (dt(12), dt(13)),
    ]
