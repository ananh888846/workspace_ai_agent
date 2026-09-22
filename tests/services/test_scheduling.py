from datetime import datetime, timedelta, timezone

import pytest

from app.services.calendar_free_busy import BusyPeriod
from app.services.scheduling import SchedulingService


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 24, hour, minute, tzinfo=timezone.utc)


def test_find_slots_when_calendar_is_free():
    slots = SchedulingService().find_available_slots(
        search_start=dt(9),
        search_end=dt(12),
        duration_minutes=60,
        busy_periods=[],
    )
    assert [(item.start, item.end) for item in slots] == [
        (dt(9), dt(10)),
        (dt(10), dt(11)),
        (dt(11), dt(12)),
    ]


def test_skips_busy_period_and_finds_next_slot():
    busy = [BusyPeriod(calendar_id="primary", start=dt(10), end=dt(11))]
    slots = SchedulingService().find_available_slots(
        search_start=dt(9),
        search_end=dt(13),
        duration_minutes=60,
        busy_periods=busy,
    )
    assert [(item.start, item.end) for item in slots] == [
        (dt(9), dt(10)),
        (dt(11), dt(12)),
        (dt(12), dt(13)),
    ]


def test_merges_overlapping_busy_periods():
    busy = [
        BusyPeriod(calendar_id="a", start=dt(10), end=dt(11)),
        BusyPeriod(calendar_id="a", start=dt(10, 30), end=dt(12)),
    ]
    slots = SchedulingService().find_available_slots(
        search_start=dt(9),
        search_end=dt(13),
        duration_minutes=60,
        busy_periods=busy,
    )
    assert [(item.start, item.end) for item in slots] == [
        (dt(9), dt(10)),
        (dt(12), dt(13)),
    ]


def test_returns_empty_when_no_window_can_fit_duration():
    busy = [BusyPeriod(calendar_id="primary", start=dt(9), end=dt(12))]
    slots = SchedulingService().find_available_slots(
        search_start=dt(9),
        search_end=dt(12),
        duration_minutes=60,
        busy_periods=busy,
    )
    assert slots == []


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"search_start": datetime(2026, 9, 24, 9), "search_end": dt(12)}, "datetime_must_be_timezone_aware"),
        ({"search_start": dt(12), "search_end": dt(11)}, "search_end_must_be_after_search_start"),
        ({"search_start": dt(9), "search_end": dt(10), "duration_minutes": 0}, "duration_minutes_must_be_positive"),
    ],
)
def test_validates_scheduling_inputs(kwargs, error):
    values = {
        "search_start": dt(9),
        "search_end": dt(10),
        "duration_minutes": 60,
        "busy_periods": [],
    }
    values.update(kwargs)
    with pytest.raises(ValueError, match=error):
        SchedulingService().find_available_slots(**values)
