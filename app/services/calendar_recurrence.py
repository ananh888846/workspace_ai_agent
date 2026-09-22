from __future__ import annotations

from dataclasses import dataclass
import re


_FREQUENCIES = {"DAILY", "WEEKLY", "MONTHLY", "YEARLY"}
_WEEKDAYS = {"MO", "TU", "WE", "TH", "FR", "SA", "SU"}
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_INT_KEYS = {"INTERVAL", "COUNT"}
_DAY_TOKEN_RE = re.compile(r"^(?:[+-]?\d{1,2})?(?:MO|TU|WE|TH|FR|SA|SU)$")


@dataclass(frozen=True)
class RecurrenceRule:
    """Quy tắc recurrence đã chuẩn hóa cho Google Calendar."""

    frequency: str
    interval: int = 1
    count: int | None = None
    until: str | None = None
    byday: tuple[str, ...] = ()

    def to_rrule(self) -> str:
        parts = [f"FREQ={self.frequency}"]
        if self.interval != 1:
            parts.append(f"INTERVAL={self.interval}")
        if self.count is not None:
            parts.append(f"COUNT={self.count}")
        if self.until is not None:
            parts.append(f"UNTIL={self.until}")
        if self.byday:
            parts.append(f"BYDAY={','.join(self.byday)}")
        return "RRULE:" + ";".join(parts)


class CalendarRecurrenceService:
    """Validate recurrence rules trước khi gửi sang Google Calendar."""

    def parse(self, value: str) -> RecurrenceRule:
        if not value or not value.startswith("RRULE:"):
            raise ValueError("recurrence_must_start_with_rrule")

        body = value[6:]
        fields: dict[str, str] = {}
        for item in body.split(";"):
            if not item or "=" not in item:
                raise ValueError("invalid_recurrence_component")
            key, raw = item.split("=", 1)
            if not _KEY_RE.fullmatch(key) or not raw:
                raise ValueError("invalid_recurrence_component")
            if key in fields:
                raise ValueError("duplicate_recurrence_component")
            fields[key] = raw

        frequency = fields.get("FREQ")
        if frequency not in _FREQUENCIES:
            raise ValueError("recurrence_frequency_required_or_unsupported")

        interval = self._positive_int(fields.get("INTERVAL", "1"), "recurrence_interval_invalid")
        count = None
        if "COUNT" in fields:
            count = self._positive_int(fields["COUNT"], "recurrence_count_invalid")

        until = fields.get("UNTIL")
        if until and count is not None:
            raise ValueError("recurrence_count_and_until_are_mutually_exclusive")
        if until and not re.fullmatch(r"\d{8}(?:T\d{6}Z)?", until):
            raise ValueError("recurrence_until_must_be_ical_datetime")

        byday: tuple[str, ...] = ()
        if "BYDAY" in fields:
            tokens = tuple(fields["BYDAY"].split(","))
            if not tokens or any(not _DAY_TOKEN_RE.fullmatch(token) for token in tokens):
                raise ValueError("recurrence_byday_invalid")
            byday = tokens

        unsupported = set(fields) - {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY"}
        if unsupported:
            raise ValueError("recurrence_component_not_supported")

        return RecurrenceRule(
            frequency=frequency,
            interval=interval,
            count=count,
            until=until,
            byday=byday,
        )

    @staticmethod
    def _positive_int(value: str, error: str) -> int:
        try:
            number = int(value)
        except ValueError as exc:
            raise ValueError(error) from exc
        if number <= 0:
            raise ValueError(error)
        return number
