from datetime import datetime
from zoneinfo import ZoneInfo

from app.main import _natural_language_calendar_start

VN = ZoneInfo("Asia/Ho_Chi_Minh")


def test_natural_start_from_tomorrow_9h():
    result = _natural_language_calendar_start("Tạo lịch họp ngày mai lúc 9h", None)
    assert result is not None
    value = datetime.fromisoformat(result)
    assert value.tzinfo is not None
    assert value.hour == 9


def test_natural_start_from_explicit_date_and_time():
    result = _natural_language_calendar_start("Tạo cuộc hẹn ngày 24/09/2026 lúc 14:30", None)
    assert result == "2026-09-24T14:30:00+07:00"


def test_explicit_start_wins_over_natural_language():
    result = _natural_language_calendar_start("Tạo lịch ngày mai lúc 9h", "2026-09-30T08:00:00+07:00")
    assert result == "2026-09-30T08:00:00+07:00"


def test_non_datetime_message_is_not_parsed():
    assert _natural_language_calendar_start("Tạo lịch họp với anh An", None) is None
