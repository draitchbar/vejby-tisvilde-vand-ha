"""API client for Vejby Tisvilde Vand."""
import logging
from datetime import datetime, timedelta
from typing import Any

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

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str):
        """Initialize the API client."""
        self._session = session
        self._email = email
        self._password = password
        self._token = None

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
        self, device_ids: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get device usage data for a period."""
        if not self._token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(API_TIMEOUT):
                response = await self._session.post(
                    f"{API_BASE_URL}/api/Stats/usage/devices",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json={
                        "DeviceIds": device_ids,
                        "QuantityType": "WaterVolume",  # Singular!
                        "Unit": "KubicMeter",
                        "Interval": "Hourly",
                        "From": start_date.isoformat(),
                        "To": end_date.isoformat(),
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
                            "Interval": "Hourly",
                            "From": start_date.isoformat(),
                            "To": end_date.isoformat(),
                        },
                    )

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching device usage: %s", err)
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def get_daily_usage(self, device_ids: list[str]) -> dict[str, float]:
        """Get daily usage for devices (today's consumption in cubic meters)."""
        # Get usage from start of today until now
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        usage_data = await self.get_device_usage(device_ids, start_of_day, now)

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
