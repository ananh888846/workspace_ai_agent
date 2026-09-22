from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.calendar_datetime import CalendarDateTimeParser

VN = ZoneInfo("Asia/Ho_Chi_Minh")


@pytest.fixture
def parser() -> CalendarDateTimeParser:
    return CalendarDateTimeParser()


def test_ngay_mai_luc_9_gio(parser: CalendarDateTimeParser) -> None:
    reference = datetime(2026, 9, 23, 15, 0, tzinfo=VN)
    result = parser.parse("ngày mai lúc 9 giờ", reference=reference)
    assert result.value == datetime(2026, 9, 24, 9, 0, tzinfo=VN)


def test_thu_sau_tuan_sau(parser: CalendarDateTimeParser) -> None:
    reference = datetime(2026, 9, 23, 15, 0, tzinfo=VN)
    result = parser.parse("thứ sáu tuần sau lúc 14:30", reference=reference)
    assert result.value == datetime(2026, 10, 2, 14, 30, tzinfo=VN)


def test_relative_hours(parser: CalendarDateTimeParser) -> None:
    reference = datetime(2026, 9, 23, 15, 0, tzinfo=VN)
    result = parser.parse("2 tiếng nữa", reference=reference)
    assert result.value == datetime(2026, 9, 23, 17, 0, tzinfo=VN)


def test_afternoon(parser: CalendarDateTimeParser) -> None:
    reference = datetime(2026, 9, 23, 10, 0, tzinfo=VN)
    result = parser.parse("ngày mai lúc 2h chiều", reference=reference)
    assert result.value == datetime(2026, 9, 24, 14, 0, tzinfo=VN)


def test_explicit_date(parser: CalendarDateTimeParser) -> None:
    reference = datetime(2026, 9, 23, 10, 0, tzinfo=VN)
    result = parser.parse("24/09/2026 lúc 08:30", reference=reference)
    assert result.value == datetime(2026, 9, 24, 8, 30, tzinfo=VN)


def test_naive_reference_is_rejected(parser: CalendarDateTimeParser) -> None:
    with pytest.raises(ValueError, match="reference_datetime_must_be_timezone_aware"):
        parser.parse("ngày mai lúc 9h", reference=datetime(2026, 9, 23, 10, 0))


def test_empty_expression_is_rejected(parser: CalendarDateTimeParser) -> None:
    with pytest.raises(ValueError, match="datetime_expression_required"):
        parser.parse("")
