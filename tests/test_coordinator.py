"""Unit tests for VejbyTisvildeVandDataUpdateCoordinator._async_update_data."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from helpers import SAMPLE_CUSTOMER_DATA
from vejby_tisvilde_vand.models import CoordinatorData, Device
from vejby_tisvilde_vand.api import VejbyTisvildeVandApi
from vejby_tisvilde_vand import VejbyTisvildeVandDataUpdateCoordinator, _parse_devices


def _make_coordinator(api):
    mock_hass = MagicMock()
    mock_hass.config.time_zone = "Europe/Copenhagen"
    coord = VejbyTisvildeVandDataUpdateCoordinator.__new__(VejbyTisvildeVandDataUpdateCoordinator)
    coord.hass = mock_hass
    coord.logger = MagicMock()
    coord.api = api
    coord.data = None
    coord.last_update_success = True
    return coord


def _make_api():
    api = MagicMock(spec=VejbyTisvildeVandApi)
    api.get_customer_details = AsyncMock(return_value=SAMPLE_CUSTOMER_DATA)
    api.get_daily_usage = AsyncMock(return_value={"dev-1": 1.0})
    api.get_yesterday_usage = AsyncMock(return_value={"dev-1": 0.5})
    api.get_monthly_usage = AsyncMock(return_value={"dev-1": 10.0})
    api.get_yearly_usage = AsyncMock(return_value={"dev-1": 100.0})
    return api


@pytest.mark.asyncio
async def test_async_update_data_returns_coordinator_data():
    api = _make_api()
    coord = _make_coordinator(api)
    result = await coord._async_update_data()

    assert isinstance(result, CoordinatorData)
    assert len(result.devices) == 1
    assert result.devices[0].id == "dev-1"
    assert result.devices[0].location_id == "loc-1"
    assert result.devices[0].location_name == "Testvej 1"
    assert result.daily_usage == {"dev-1": 1.0}
    assert result.yesterday_usage == {"dev-1": 0.5}
    assert result.monthly_usage == {"dev-1": 10.0}
    assert result.yearly_usage == {"dev-1": 100.0}


@pytest.mark.asyncio
async def test_async_update_data_groups_devices_by_location():
    """Two devices in the same location → one usage call per type."""
    multi_customer = {
        "Locations": [
            {
                "LocationId": "loc-1",
                "Address": "A",
                "Devices": [
                    {"Id": "dev-1", "DeviceType": "WaterMeter"},
                    {"Id": "dev-2", "DeviceType": "WaterMeter"},
                ],
            }
        ]
    }
    api = _make_api()
    api.get_customer_details = AsyncMock(return_value=multi_customer)
    api.get_daily_usage = AsyncMock(return_value={"dev-1": 1.0})
    api.get_yesterday_usage = AsyncMock(return_value={"dev-1": 0.5})
    api.get_monthly_usage = AsyncMock(return_value={"dev-1": 10.0})
    api.get_yearly_usage = AsyncMock(return_value={"dev-1": 100.0})

    coord = _make_coordinator(api)
    result = await coord._async_update_data()

    api.get_daily_usage.assert_called_once_with("loc-1", ["dev-1", "dev-2"])
    assert len(result.devices) == 2


@pytest.mark.asyncio
async def test_async_update_data_no_devices_returns_empty():
    api = _make_api()
    api.get_customer_details = AsyncMock(return_value={"Locations": []})
    coord = _make_coordinator(api)
    result = await coord._async_update_data()

    assert isinstance(result, CoordinatorData)
    assert result.devices == []
    assert result.daily_usage == {}


def test_parse_devices_extracts_correctly():
    devices = _parse_devices(SAMPLE_CUSTOMER_DATA)
    assert len(devices) == 1
    assert devices[0].id == "dev-1"
    assert devices[0].location_id == "loc-1"
    assert devices[0].device_type == "WaterMeter"
