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
    """Tìm các khoảng thời gian trống từ dữ liệu Free/Busy đã được kiểm soát."""

    def find_available_slots(
        self,
        *,
        search_start: datetime,
        search_end: datetime,
        duration_minutes: int,
        busy_periods: list[BusyPeriod],
        max_results: int = 5,
    ) -> list[AvailableSlot]:
        if search_start.tzinfo is None or search_end.tzinfo is None:
            raise ValueError("datetime_must_be_timezone_aware")
        if search_end <= search_start:
            raise ValueError("search_end_must_be_after_search_start")
        if duration_minutes <= 0:
            raise ValueError("duration_minutes_must_be_positive")
        if max_results <= 0:
            raise ValueError("max_results_must_be_positive")

        duration = timedelta(minutes=duration_minutes)
        normalized = sorted(
            (
                period
                for period in busy_periods
                if period.start.tzinfo is not None
                and period.end.tzinfo is not None
                and period.end > period.start
            ),
            key=lambda period: period.start,
        )

        merged: list[BusyPeriod] = []
        for period in normalized:
            if period.start >= search_end or period.end <= search_start:
                continue
            start = max(period.start, search_start)
            end = min(period.end, search_end)
            if not merged or start > merged[-1].end:
                merged.append(
                    BusyPeriod(
                        calendar_id=period.calendar_id,
                        start=start,
                        end=end,
                    )
                )
            elif end > merged[-1].end:
                previous = merged[-1]
                merged[-1] = BusyPeriod(
                    calendar_id=previous.calendar_id,
                    start=previous.start,
                    end=end,
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
