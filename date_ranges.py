"""Date range providers for Vejby Tisvilde Vand integration."""
from datetime import datetime, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo


class DateRangeProvider(Protocol):
    """Protocol for date range providers."""

    def today_range(self) -> tuple[datetime, datetime]: ...
    def yesterday_range(self) -> tuple[datetime, datetime]: ...
    def month_to_date_range(self) -> tuple[datetime, datetime]: ...
    def year_to_date_range(self) -> tuple[datetime, datetime]: ...


class TimezoneAwareDateRangeProvider:
    """Date range provider that computes ranges in a given timezone."""

    def __init__(self, timezone: str) -> None:
        """Initialize with timezone string, e.g. 'Europe/Copenhagen'."""
        self._tz = ZoneInfo(timezone)

    def _now(self) -> datetime:
        return datetime.now(self._tz)

    def today_range(self) -> tuple[datetime, datetime]:
        """From midnight today until now."""
        now = self._now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    def yesterday_range(self) -> tuple[datetime, datetime]:
        """Full day yesterday (00:00 – 23:59:59.999999)."""
        now = self._now()
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def month_to_date_range(self) -> tuple[datetime, datetime]:
        """From the 1st of the current month until now."""
        now = self._now()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now

    def year_to_date_range(self) -> tuple[datetime, datetime]:
        """From January 1st of the current year until now."""
        now = self._now()
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now
