"""Unit tests for TimezoneAwareDateRangeProvider."""
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from vejby_tisvilde_vand.date_ranges import TimezoneAwareDateRangeProvider

TZ = "Europe/Copenhagen"
FIXED_NOW = datetime(2026, 3, 7, 14, 30, 0, tzinfo=ZoneInfo(TZ))


@pytest.fixture
def provider():
    p = TimezoneAwareDateRangeProvider(TZ)
    with patch.object(p, "_now", return_value=FIXED_NOW):
        yield p


def test_today_range_start_is_midnight(provider):
    start, end = provider.today_range()
    assert start.hour == 0 and start.minute == 0 and start.second == 0
    assert start.day == FIXED_NOW.day


def test_today_range_end_is_now(provider):
    _, end = provider.today_range()
    assert end == FIXED_NOW


def test_yesterday_range_spans_full_day(provider):
    start, end = provider.yesterday_range()
    expected_day = FIXED_NOW.day - 1
    assert start.day == expected_day
    assert start.hour == 0 and start.minute == 0
    assert end.day == expected_day
    assert end.hour == 23 and end.minute == 59 and end.second == 59


def test_month_to_date_range_starts_first_of_month(provider):
    start, end = provider.month_to_date_range()
    assert start.day == 1
    assert start.month == FIXED_NOW.month
    assert end == FIXED_NOW


def test_year_to_date_range_starts_jan_first(provider):
    start, end = provider.year_to_date_range()
    assert start.month == 1 and start.day == 1
    assert start.year == FIXED_NOW.year
    assert end == FIXED_NOW


def test_ranges_are_timezone_aware(provider):
    for fn in (provider.today_range, provider.yesterday_range,
               provider.month_to_date_range, provider.year_to_date_range):
        start, end = fn()
        assert start.tzinfo is not None
        assert end.tzinfo is not None
