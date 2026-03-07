"""Shared test helpers, constants, and mock classes.

Note: HA stubs are installed by the root conftest.py before any test module loads.
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock


# ---------------------------------------------------------------------------
# Sample API response dicts
# ---------------------------------------------------------------------------

SAMPLE_CUSTOMER_DATA = {
    "Locations": [
        {
            "LocationId": "loc-1",
            "Address": "Testvej 1",
            "Devices": [
                {"Id": "dev-1", "DeviceType": "WaterMeter"},
            ],
        }
    ]
}

SAMPLE_USAGE_RESPONSE = {"TotalUsage": 2.5, "Buckets": []}

# Fixed "now" for deterministic date range tests
FIXED_NOW = datetime(2026, 3, 7, 14, 30, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Mock HTTP client
# ---------------------------------------------------------------------------

class MockHttpClient:
    def __init__(self):
        self.get = AsyncMock()
        self.post = AsyncMock()


# ---------------------------------------------------------------------------
# Mock date range provider
# ---------------------------------------------------------------------------

class MockDateRangeProvider:
    def today_range(self):
        start = FIXED_NOW.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, FIXED_NOW

    def yesterday_range(self):
        yesterday = FIXED_NOW - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end

    def month_to_date_range(self):
        start = FIXED_NOW.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, FIXED_NOW

    def year_to_date_range(self):
        start = FIXED_NOW.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, FIXED_NOW


# ---------------------------------------------------------------------------
# .env loader for functional tests
# ---------------------------------------------------------------------------

def load_dotenv_credentials():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            pass
    return os.getenv("VEJBY_EMAIL"), os.getenv("VEJBY_PASSWORD")
