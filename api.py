"""API client for Vejby Tisvilde Vand."""
import logging
from datetime import timezone
from typing import Any

from .const import API_BASE_URL
from .date_ranges import DateRangeProvider, TimezoneAwareDateRangeProvider
from .http_client import AioHttpClient, HttpClient, HttpError

_LOGGER = logging.getLogger(__name__)


class VejbyTisvildeVandApiError(Exception):
    """Base exception for API errors."""


class VejbyTisvildeVandAuthError(VejbyTisvildeVandApiError):
    """Exception for authentication errors."""


class VejbyTisvildeVandApi:
    """API client for Vejby Tisvilde Vand."""

    def __init__(
        self,
        http_client: HttpClient,
        email: str,
        password: str,
        date_ranges: DateRangeProvider,
    ) -> None:
        self._http = http_client
        self._email = email
        self._password = password
        self._date_ranges = date_ranges
        self._token: str | None = None

    async def authenticate(self) -> bool:
        """Authenticate and store the Bearer token."""
        try:
            data = await self._http.post(
                f"{API_BASE_URL}/api/Customer/login",
                json={"email": self._email, "password": self._password},
            )
            self._token = data.get("AuthToken")
            return True
        except HttpError as err:
            if err.status_code == 401:
                raise VejbyTisvildeVandAuthError("Invalid email or password") from err
            raise VejbyTisvildeVandApiError(f"HTTP error {err.status_code}") from err
        except Exception as err:
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def _request_get(self, url: str, params: dict | None = None) -> Any:
        """GET with auth header; re-authenticates once on 401."""
        if not self._token:
            await self.authenticate()
        try:
            return await self._http.get(url, headers={"Authorization": f"Bearer {self._token}"}, params=params or {})
        except HttpError as err:
            if err.status_code == 401:
                await self.authenticate()
                try:
                    return await self._http.get(url, headers={"Authorization": f"Bearer {self._token}"}, params=params or {})
                except HttpError as retry_err:
                    raise VejbyTisvildeVandApiError(f"HTTP error {retry_err.status_code}") from retry_err
            raise VejbyTisvildeVandApiError(f"HTTP error {err.status_code}") from err
        except Exception as err:
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def _request_post(self, url: str, json: dict) -> Any:
        """POST with auth header; re-authenticates once on 401."""
        if not self._token:
            await self.authenticate()
        try:
            return await self._http.post(url, json=json, headers={"Authorization": f"Bearer {self._token}"})
        except HttpError as err:
            if err.status_code == 401:
                await self.authenticate()
                try:
                    return await self._http.post(url, json=json, headers={"Authorization": f"Bearer {self._token}"})
                except HttpError as retry_err:
                    raise VejbyTisvildeVandApiError(f"HTTP error {retry_err.status_code}") from retry_err
            raise VejbyTisvildeVandApiError(f"HTTP error {err.status_code}") from err
        except Exception as err:
            raise VejbyTisvildeVandApiError(f"Connection error: {err}") from err

    async def get_customer_details(self, include_disabled_devices: bool = False) -> dict[str, Any]:
        """Get customer details including devices."""
        return await self._request_get(
            f"{API_BASE_URL}/api/Customer",
            params={"IncludeDisabledDevices": "true" if include_disabled_devices else "false"},
        )

    async def get_device_usage(
        self, location_id: str, device_ids: list[str], start_date, end_date, interval: str = "Hourly"
    ) -> dict[str, Any]:
        """Get device usage data for a period with specified interval granularity."""
        start_utc = start_date.astimezone(timezone.utc)
        end_utc = end_date.astimezone(timezone.utc)
        return await self._request_post(
            f"{API_BASE_URL}/api/Stats/usage/{location_id}/devices",
            json={
                "DeviceIds": device_ids,
                "QuantityType": "WaterVolume",
                "Unit": "KubicMeter",
                "Interval": interval,
                "From": start_utc.isoformat(),
                "To": end_utc.isoformat(),
            },
        )

    def _parse_total_usage(self, usage_data: dict[str, Any], device_ids: list[str]) -> dict[str, float]:
        """Extract TotalUsage from an API response and assign it to the first device ID."""
        if not isinstance(usage_data, dict) or not device_ids:
            return {}
        total = usage_data.get("TotalUsage", 0.0)
        return {device_ids[0]: float(total) if total else 0.0}

    async def get_daily_usage(self, location_id: str, device_ids: list[str]) -> dict[str, float]:
        """Get today's consumption from midnight until now."""
        start, end = self._date_ranges.today_range()
        usage_data = await self.get_device_usage(location_id, device_ids, start, end, interval="Hourly")
        return self._parse_total_usage(usage_data, device_ids)

    async def get_yesterday_usage(self, location_id: str, device_ids: list[str]) -> dict[str, float]:
        """Get yesterday's total consumption."""
        start, end = self._date_ranges.yesterday_range()
        usage_data = await self.get_device_usage(location_id, device_ids, start, end, interval="Hourly")
        return self._parse_total_usage(usage_data, device_ids)

    async def get_monthly_usage(self, location_id: str, device_ids: list[str]) -> dict[str, float]:
        """Get month-to-date consumption."""
        start, end = self._date_ranges.month_to_date_range()
        usage_data = await self.get_device_usage(location_id, device_ids, start, end, interval="Daily")
        return self._parse_total_usage(usage_data, device_ids)

    async def get_yearly_usage(self, location_id: str, device_ids: list[str]) -> dict[str, float]:
        """Get year-to-date consumption."""
        start, end = self._date_ranges.year_to_date_range()
        usage_data = await self.get_device_usage(location_id, device_ids, start, end, interval="Monthly")
        return self._parse_total_usage(usage_data, device_ids)
