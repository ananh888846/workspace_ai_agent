from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BusyPeriod:
    """Khoảng thời gian một calendar đang bận."""

    calendar_id: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class Conflict:
    """Một khoảng busy giao với khoảng thời gian được đề xuất."""

    calendar_id: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class ConflictResult:
    """Kết quả kiểm tra xung đột theo các khoảng busy đã chuẩn hóa."""

    has_conflict: bool
    conflicts: tuple[Conflict, ...]


class CalendarConflictDetector:
    """Tính conflict thuần Python, không biết provider hay database."""

    def detect(
        self,
        *,
        requested_start: datetime,
        requested_end: datetime,
        busy_periods: list[BusyPeriod],
    ) -> ConflictResult:
        if requested_start.tzinfo is None or requested_end.tzinfo is None:
            raise ValueError("datetime_must_be_timezone_aware")
        if requested_end <= requested_start:
            raise ValueError("requested_end_must_be_after_start")

        conflicts = tuple(
            Conflict(
                calendar_id=period.calendar_id,
                start=period.start,
                end=period.end,
            )
            for period in busy_periods
            if period.start.tzinfo is not None
            and period.end.tzinfo is not None
            and period.start < requested_end
            and period.end > requested_start
        )
        return ConflictResult(has_conflict=bool(conflicts), conflicts=conflicts)
