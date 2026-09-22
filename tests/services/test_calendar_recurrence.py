import pytest

from app.services.calendar_recurrence import CalendarRecurrenceService


def test_parse_weekly_recurrence():
    rule = CalendarRecurrenceService().parse(
        "RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR;COUNT=6"
    )
    assert rule.frequency == "WEEKLY"
    assert rule.interval == 2
    assert rule.count == 6
    assert rule.byday == ("MO", "WE", "FR")
    assert rule.to_rrule() == "RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=6;BYDAY=MO,WE,FR"


def test_parse_until_recurrence():
    rule = CalendarRecurrenceService().parse(
        "RRULE:FREQ=MONTHLY;UNTIL=20261231T000000Z"
    )
    assert rule.until == "20261231T000000Z"


@pytest.mark.parametrize(
    "value,error",
    [
        ("FREQ=DAILY", "recurrence_must_start_with_rrule"),
        ("RRULE:FREQ=HOURLY", "recurrence_frequency_required_or_unsupported"),
        ("RRULE:FREQ=WEEKLY;COUNT=0", "recurrence_count_invalid"),
        (
            "RRULE:FREQ=DAILY;COUNT=2;UNTIL=20261231T000000Z",
            "recurrence_count_and_until_are_mutually_exclusive",
        ),
        ("RRULE:FREQ=WEEKLY;BYDAY=XX", "recurrence_byday_invalid"),
        ("RRULE:FREQ=DAILY;BYHOUR=9", "recurrence_component_not_supported"),
    ],
)
def test_rejects_invalid_recurrence(value, error):
    with pytest.raises(ValueError, match=error):
        CalendarRecurrenceService().parse(value)
