from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

_WEEKDAY_NAMES = {
    "thu 2": 0, "thứ 2": 0, "thu hai": 0, "thứ hai": 0,
    "thu 3": 1, "thứ 3": 1, "thu ba": 1, "thứ ba": 1,
    "thu 4": 2, "thứ 4": 2, "thu tu": 2, "thứ tư": 2,
    "thu 5": 3, "thứ 5": 3, "thu nam": 3, "thứ năm": 3,
    "thu 6": 4, "thứ 6": 4, "thu sau": 4, "thứ sáu": 4,
    "thu 7": 5, "thứ 7": 5, "thu bay": 5, "thứ bảy": 5,
    "chu nhat": 6, "chủ nhật": 6,
}

_TIME_PARTS = {
    "sáng": (6, 11),
    "trưa": (11, 14),
    "chiều": (13, 18),
    "tối": (18, 23),
}


@dataclass(frozen=True)
class CalendarDateTimeResult:
    """Kết quả chuẩn hóa thời gian lịch theo múi giờ Việt Nam."""

    value: datetime
    timezone: str = "Asia/Ho_Chi_Minh"


class CalendarDateTimeParser:
    """Parser nhẹ bằng Python cho ngày giờ tự nhiên tiếng Việt."""

    def parse(self, text: str, *, reference: datetime | None = None) -> CalendarDateTimeResult:
        """Phân tích một biểu thức ngày giờ và trả về datetime có timezone."""
        if not text or not text.strip():
            raise ValueError("datetime_expression_required")

        reference_local = self._reference_local(reference)
        normalized = self._normalize(text)

        relative = self._parse_relative_duration(normalized, reference_local)
        if relative is not None:
            return CalendarDateTimeResult(relative)

        target_date = self._parse_date(normalized, reference_local.date())
        target_time = self._parse_time(normalized)

        if target_time is None:
            target_time = time(9, 0)

        value = datetime.combine(target_date, target_time, tzinfo=VIETNAM_TIMEZONE)

        if (
            target_date == reference_local.date()
            and value < reference_local
            and not self._has_explicit_date(normalized)
        ):
            if self._has_explicit_today(normalized):
                raise ValueError("datetime_expression_is_in_the_past")
            tomorrow = target_date + timedelta(days=1)
            value = datetime.combine(tomorrow, target_time, tzinfo=VIETNAM_TIMEZONE)

        return CalendarDateTimeResult(value)

    @staticmethod
    def _reference_local(reference: datetime | None) -> datetime:
        if reference is None:
            return datetime.now(VIETNAM_TIMEZONE)
        if reference.tzinfo is None:
            raise ValueError("reference_datetime_must_be_timezone_aware")
        return reference.astimezone(VIETNAM_TIMEZONE)

    @staticmethod
    def _normalize(text: str) -> str:
        value = " ".join(text.casefold().strip().split())
        return value.replace("giờ", "h")

    @staticmethod
    def _has_explicit_today(text: str) -> bool:
        return "hôm nay" in text

    @staticmethod
    def _has_explicit_date(text: str) -> bool:
        return re.search(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", text) is not None

    def _parse_relative_duration(self, text: str, reference: datetime) -> datetime | None:
        match = re.search(r"\b(\d+)\s*(phút|p|giờ|h|tiếng)\s*(nữa|sau)\b", text)
        if not match:
            return None
        amount = int(match.group(1))
        unit = match.group(2)
        if unit in {"phút", "p"}:
            return reference + timedelta(minutes=amount)
        return reference + timedelta(hours=amount)

    def _parse_date(self, text: str, reference_date: date) -> date:
        if "ngày kia" in text:
            return reference_date + timedelta(days=2)
        if "ngày mai" in text or "mai" in text:
            return reference_date + timedelta(days=1)
        if "hôm nay" in text:
            return reference_date

        week_match = re.search(r"(?:tuần sau|tuan sau)\s+(?:thứ|thu)\s*([2-7])", text)
        if week_match:
            return self._next_weekday(reference_date, int(week_match.group(1)) - 2, weeks=1)

        for name, weekday in sorted(_WEEKDAY_NAMES.items(), key=lambda item: -len(item[0])):
            if name in text:
                weeks = 1 if "tuần sau" in text or "tuan sau" in text else 0
                return self._next_weekday(reference_date, weekday, weeks=weeks)

        explicit = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
        if explicit:
            day = int(explicit.group(1))
            month = int(explicit.group(2))
            year_text = explicit.group(3)
            year = reference_date.year if year_text is None else int(year_text)
            if year < 100:
                year += 2000
            return date(year, month, day)

        return reference_date

    @staticmethod
    def _next_weekday(reference_date: date, weekday: int, *, weeks: int) -> date:
        days_ahead = (weekday - reference_date.weekday()) % 7
        if weeks:
            days_ahead += 7
        return reference_date + timedelta(days=days_ahead)

    def _parse_time(self, text: str) -> time | None:
        # Chỉ coi số là giờ khi có dấu ':' hoặc ký hiệu 'h', tránh nhầm ngày 24/09/2026 thành giờ 24.
        match = re.search(
            r"\b(?:(\d{1,2}):(\d{2})\b|(\d{1,2})h\s*(\d{2})?\b)\s*(sáng|trưa|chiều|tối)?",
            text,
        )
        if not match:
            return None

        if match.group(1) is not None:
            hour = int(match.group(1))
            minute = int(match.group(2))
        else:
            hour = int(match.group(3))
            minute = int(match.group(4) or 0)

        period = match.group(5)

        if period == "chiều" and hour < 12:
            hour += 12
        elif period == "tối" and hour < 12:
            hour += 12
        elif period == "trưa" and hour < 11:
            hour += 12

        if hour > 23 or minute > 59:
            raise ValueError("invalid_time")
        return time(hour, minute)
