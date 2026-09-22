from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.calendar_free_busy import BusyPeriod


@dataclass(frozen=True)
class AvailableSlot:
    """Khoảng thời gian còn trống phù hợp với thời lượng yêu cầu."""

    start: datetime
    end: datetime


class SchedulingService:
    """Tìm khoảng thời gian trống từ dữ liệu Free/Busy đã được kiểm soát."""

    def find_conflicts(
        self,
        *,
        search_start: datetime,
        search_end: datetime,
        busy_periods: list[BusyPeriod],
    ) -> list[BusyPeriod]:
        """Lọc các khoảng bận giao với cửa sổ tìm kiếm."""
        self._validate_window(search_start, search_end)

        conflicts: list[BusyPeriod] = []
        for period in busy_periods:
            if period.start.tzinfo is None or period.end.tzinfo is None:
                continue
            if period.end <= period.start:
                continue
            if period.start < search_end and period.end > search_start:
                conflicts.append(
                    BusyPeriod(
                        calendar_id=period.calendar_id,
                        start=max(period.start, search_start),
                        end=min(period.end, search_end),
                    )
                )
        return sorted(conflicts, key=lambda period: period.start)

    def find_available_slots(
        self,
        *,
        search_start: datetime,
        search_end: datetime,
        duration_minutes: int,
        busy_periods: list[BusyPeriod],
        max_results: int = 5,
    ) -> list[AvailableSlot]:
        """Tìm các slot liên tiếp, không giao với dữ liệu Free/Busy."""
        self._validate_window(search_start, search_end)
        if duration_minutes <= 0:
            raise ValueError("duration_minutes_must_be_positive")
        if max_results <= 0:
            raise ValueError("max_results_must_be_positive")

        duration = timedelta(minutes=duration_minutes)
        normalized = self.find_conflicts(
            search_start=search_start,
            search_end=search_end,
            busy_periods=busy_periods,
        )

        merged: list[BusyPeriod] = []
        for period in normalized:
            if not merged or period.start > merged[-1].end:
                merged.append(period)
            elif period.end > merged[-1].end:
                previous = merged[-1]
                merged[-1] = BusyPeriod(
                    calendar_id=previous.calendar_id,
                    start=previous.start,
                    end=period.end,
                )

        slots: list[AvailableSlot] = []
        cursor = search_start

        for period in merged:
            while period.start - cursor >= duration:
                slots.append(AvailableSlot(start=cursor, end=cursor + duration))
                if len(slots) >= max_results:
                    return slots
                cursor += duration

            if period.end > cursor:
                cursor = period.end

        while search_end - cursor >= duration:
            slots.append(AvailableSlot(start=cursor, end=cursor + duration))
            if len(slots) >= max_results:
                return slots
            cursor += duration

        return slots

    @staticmethod
    def _validate_window(search_start: datetime, search_end: datetime) -> None:
        """Kiểm tra cửa sổ tìm kiếm phải có timezone và thứ tự hợp lệ."""
        if search_start.tzinfo is None or search_end.tzinfo is None:
            raise ValueError("datetime_must_be_timezone_aware")
        if search_end <= search_start:
            raise ValueError("search_end_must_be_after_search_start")
