"""API client for Vejby Tisvilde Vand."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp
import async_timeout

from .const import API_BASE_URL, API_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class VejbyTisvildeVandApiError(Exception):
    """Base exception for API errors."""


class VejbyTisvildeVandAuthError(VejbyTisvildeVandApiError):
    """Exception for authentication errors."""


class VejbyTisvildeVandApi:
    """API client for Vejby Tisvilde Vand."""

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str, timezone: str = "UTC"):
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._token = None
        self._timezone = ZoneInfo(timezone)

    async def authenticate(self) -> bool:
        """Authenticate with the API."""
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{API_BASE_URL}/api/Customer/login",
                    json={"email": self._email, "password": self._password},
                )

                if response.status == 401:
                    raise VejbyTisvildeVandAuthError("Invalid email or password")

                response.raise_for_status()
                data = await response.json()
                self._token = data.get("AuthToken")
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error("Error authenticating with API: %s", err)
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def get_customer_details(self, include_disabled_devices: bool = False) -> dict[str, Any]:
        """Get customer details including devices."""
        if not self._token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.get(
                    f"{API_BASE_URL}/api/Customer",
                    headers={"Authorization": f"Bearer {self._token}"},
                    params={"IncludeDisabledDevices": "true" if include_disabled_devices else "false"},
                )

                if response.status == 401:
                    # Token might be expired, try to re-authenticate
                    await self.authenticate()
                    response = await self._session.get(
                        f"{API_BASE_URL}/api/Customer",
                        headers={"Authorization": f"Bearer {self._token}"},
                        params={"IncludeDisabledDevices": "true" if include_disabled_devices else "false"},
                    )

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching customer details: %s", err)
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def get_device_usage(
        self, device_ids: list[str], start_date: datetime, end_date: datetime, interval: str = "Hourly"
    ) -> dict[str, Any]:
        """Get device usage data for a period with specified interval granularity."""
        if not self._token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                # Convert timezone-aware datetimes to UTC for the API
                start_utc = start_date.astimezone(timezone.utc)
                end_utc = end_date.astimezone(timezone.utc)

                response = await self._session.post(
                    f"{API_BASE_URL}/api/Stats/usage/devices",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={
                        "DeviceIds": device_ids,
                        "QuantityType": "WaterVolume",  # Singular!
                        "Unit": "KubicMeter",
                        "Interval": interval,
                        "From": start_utc.isoformat(),
                        "To": end_utc.isoformat(),
                    },
                )

                if response.status == 401:
                    # Token might be expired, try to re-authenticate
                    await self.authenticate()
                    response = await self._session.post(
                        f"{API_BASE_URL}/api/Stats/usage/devices",
                        headers={"Authorization": f"Bearer {self._token}"},
                        json={
                            "DeviceIds": device_ids,
                            "QuantityType": "WaterVolume",  # Singular!
                            "Unit": "KubicMeter",
                            "Interval": interval,
                            "From": start_utc.isoformat(),
                            "To": end_utc.isoformat(),
                        },
                    )

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching device usage: %s", err)
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def get_daily_usage(self, device_ids: list[str]) -> dict[str, float]:
        """Get daily usage for devices (today's consumption in cubic meters)."""
        # Get usage from start of today until now with hourly granularity (in local timezone)
        now = datetime.now(self._timezone)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        usage_data = await self.get_device_usage(device_ids, start_of_day, now, interval="Hourly")

        # The API returns a single response with TotalUsage field
        # Response format: {"Unit": "KubicMeter", "QuantityType": "WaterVolume", "TotalUsage": 0.145, ...}
        daily_usage = {}

        if isinstance(usage_data, dict):
            # The API appears to return data for a single device per call
            # Use TotalUsage field from the response
            total = usage_data.get("TotalUsage", 0.0)

            # Assign this total to the first device ID (assuming single device response)
            if device_ids:
                daily_usage[device_ids[0]] = float(total) if total else 0.0

        return daily_usage

    async def get_yesterday_usage(self, device_ids: list[str]) -> dict[str, float]:
        """Get yesterday's usage for devices (yesterday's consumption in cubic meters)."""
        # Get usage for the entire previous day (in local timezone)
        now = datetime.now(self._timezone)
        yesterday = now - timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        usage_data = await self.get_device_usage(device_ids, start_of_yesterday, end_of_yesterday, interval="Hourly")

        # The API returns a single response with TotalUsage field
        yesterday_usage = {}

        if isinstance(usage_data, dict):
            total = usage_data.get("TotalUsage", 0.0)

            # Assign this total to the first device ID (assuming single device response)
            if device_ids:
                yesterday_usage[device_ids[0]] = float(total) if total else 0.0

        return yesterday_usage

    async def get_monthly_usage(self, device_ids: list[str]) -> dict[str, float]:
        """Get monthly usage for devices (this month's consumption in cubic meters)."""
        # Get usage from start of this month until now with daily granularity (more efficient, in local timezone)
        now = datetime.now(self._timezone)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        usage_data = await self.get_device_usage(device_ids, start_of_month, now, interval="Daily")

        # The API returns a single response with TotalUsage field
        monthly_usage = {}

        if isinstance(usage_data, dict):
            total = usage_data.get("TotalUsage", 0.0)

            # Assign this total to the first device ID (assuming single device response)
            if device_ids:
                monthly_usage[device_ids[0]] = float(total) if total else 0.0

        return monthly_usage

    async def get_yearly_usage(self, device_ids: list[str]) -> dict[str, float]:
        """Get yearly usage for devices (year-to-date consumption in cubic meters)."""
        # Get usage from start of this year until now with monthly granularity (more efficient, in local timezone)
        now = datetime.now(self._timezone)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        usage_data = await self.get_device_usage(device_ids, start_of_year, now, interval="Monthly")

        # The API returns a single response with TotalUsage field
        yearly_usage = {}

        if isinstance(usage_data, dict):
            total = usage_data.get("TotalUsage", 0.0)

            # Assign this total to the first device ID (assuming single device response)
            if device_ids:
                yearly_usage[device_ids[0]] = float(total) if total else 0.0

        return yearly_usage

    async def get_latest_readings(self, device_ids: list[str]) -> dict[str, Any]:
        """Get the latest readings for devices."""
        if not self._token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{API_BASE_URL}/api/Stats/readings/devices",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={
                        "DeviceIds": device_ids,
                        "QuantityType": "WaterVolume",  # Singular!
                        "Unit": "KubicMeter",
                    },
                )

                if response.status == 401:
                    # Token might be expired, try to re-authenticate
                    await self.authenticate()
                    response = await self._session.post(
                        f"{API_BASE_URL}/api/Stats/readings/devices",
                        headers={"Authorization": f"Bearer {self._token}"},
                        json={
                            "DeviceIds": device_ids,
                            "QuantityType": "WaterVolume",  # Singular!
                            "Unit": "KubicMeter",
                        },
                    )

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching latest readings: %s", err)
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err
