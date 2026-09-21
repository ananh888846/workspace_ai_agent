from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def utc_now() -> datetime:
    """Lấy thời điểm hiện tại dưới dạng datetime có timezone UTC."""
    return datetime.now(timezone.utc)


def to_utc(value: datetime) -> datetime:
    """Chuẩn hóa datetime về UTC để ghi database hoặc giao tiếp nội bộ."""
    if value.tzinfo is None:
        raise ValueError("datetime_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def to_vietnam_time(value: datetime) -> datetime:
    """Chuyển datetime có timezone sang múi giờ Việt Nam khi hiển thị."""
    if value.tzinfo is None:
        raise ValueError("datetime_must_be_timezone_aware")
    return value.astimezone(VIETNAM_TIMEZONE)
