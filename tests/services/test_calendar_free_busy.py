from datetime import datetime, timezone

import pytest

from app.services.calendar_free_busy import BusyPeriod, CalendarConflictDetector


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 25, hour, minute, tzinfo=timezone.utc)


def test_no_conflict_when_requested_interval_touches_busy_end() -> None:
    result = CalendarConflictDetector().detect(
        requested_start=dt(15),
        requested_end=dt(16),
        busy_periods=[BusyPeriod("primary", dt(14), dt(15))],
    )
    assert result.has_conflict is False
    assert result.conflicts == ()


def test_conflict_when_requested_interval_overlaps_busy_period() -> None:
    result = CalendarConflictDetector().detect(
        requested_start=dt(14, 30),
        requested_end=dt(15, 30),
        busy_periods=[BusyPeriod("primary", dt(14), dt(15))],
    )
    assert result.has_conflict is True
    assert len(result.conflicts) == 1
    assert result.conflicts[0].calendar_id == "primary"


def test_multiple_calendar_conflicts_are_returned() -> None:
    result = CalendarConflictDetector().detect(
        requested_start=dt(14),
        requested_end=dt(16),
        busy_periods=[
            BusyPeriod("work", dt(13), dt(15)),
            BusyPeriod("family", dt(15, 30), dt(17)),
        ],
    )
    assert result.has_conflict is True
    assert {item.calendar_id for item in result.conflicts} == {"work", "family"}


def test_timezone_aware_datetime_is_required() -> None:
    with pytest.raises(ValueError, match="datetime_must_be_timezone_aware"):
        CalendarConflictDetector().detect(
            requested_start=datetime(2026, 9, 25, 14),
            requested_end=dt(15),
            busy_periods=[],
        )


def test_requested_end_must_be_after_start() -> None:
    with pytest.raises(ValueError, match="requested_end_must_be_after_start"):
        CalendarConflictDetector().detect(
            requested_start=dt(15),
            requested_end=dt(14),
            busy_periods=[],
        )
