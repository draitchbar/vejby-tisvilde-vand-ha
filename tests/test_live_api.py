"""Functional tests against the real Vejby Tisvilde Vand API.

Skipped unless VEJBY_EMAIL and VEJBY_PASSWORD environment variables are set
(e.g. via a .env file in the project root).
"""
import importlib
import sys
import pytest

from helpers import load_dotenv_credentials


def _skip_if_no_creds():
    email, password = load_dotenv_credentials()
    if not email or not password:
        pytest.skip("VEJBY_EMAIL / VEJBY_PASSWORD not set")
    return email, password


@pytest.fixture
async def live_api():
    email, password = _skip_if_no_creds()

    # conftest installed mocks for aiohttp/async_timeout — remove them so the
    # real libraries are loaded for live HTTP calls.
    sys.modules.pop("aiohttp", None)
    sys.modules.pop("async_timeout", None)
    real_aiohttp = importlib.import_module("aiohttp")
    real_async_timeout = importlib.import_module("async_timeout")
    sys.modules["aiohttp"] = real_aiohttp
    sys.modules["async_timeout"] = real_async_timeout

    # Patch the already-loaded http_client module so its async_timeout reference
    # points to the real library (it was bound at import time to the mock).
    import vejby_tisvilde_vand.http_client as _hc
    _hc.async_timeout = real_async_timeout

    from vejby_tisvilde_vand.http_client import AioHttpClient
    from vejby_tisvilde_vand.date_ranges import TimezoneAwareDateRangeProvider
    from vejby_tisvilde_vand.api import VejbyTisvildeVandApi

    async with real_aiohttp.ClientSession() as session:
        api = VejbyTisvildeVandApi(
            AioHttpClient(session),
            email,
            password,
            TimezoneAwareDateRangeProvider("Europe/Copenhagen"),
        )
        yield api


@pytest.mark.asyncio
async def test_live_authenticate(live_api):
    result = await live_api.authenticate()
    assert result is True
    assert live_api._token is not None


@pytest.mark.asyncio
async def test_live_get_customer_details(live_api):
    await live_api.authenticate()
    data = await live_api.get_customer_details()
    assert "Locations" in data
    assert len(data["Locations"]) > 0


@pytest.mark.asyncio
async def test_live_daily_usage(live_api):
    await live_api.authenticate()
    data = await live_api.get_customer_details()
    location = data["Locations"][0]
    loc_id = location["LocationId"]
    device_ids = [d["Id"] for d in location["Devices"]]
    result = await live_api.get_daily_usage(loc_id, device_ids)
    assert isinstance(result, dict)
    assert device_ids[0] in result


@pytest.mark.asyncio
async def test_live_yesterday_usage(live_api):
    await live_api.authenticate()
    data = await live_api.get_customer_details()
    location = data["Locations"][0]
    loc_id = location["LocationId"]
    device_ids = [d["Id"] for d in location["Devices"]]
    result = await live_api.get_yesterday_usage(loc_id, device_ids)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_live_monthly_usage(live_api):
    await live_api.authenticate()
    data = await live_api.get_customer_details()
    location = data["Locations"][0]
    loc_id = location["LocationId"]
    device_ids = [d["Id"] for d in location["Devices"]]
    result = await live_api.get_monthly_usage(loc_id, device_ids)
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_live_yearly_usage(live_api):
    await live_api.authenticate()
    data = await live_api.get_customer_details()
    location = data["Locations"][0]
    loc_id = location["LocationId"]
    device_ids = [d["Id"] for d in location["Devices"]]
    result = await live_api.get_yearly_usage(loc_id, device_ids)
    assert isinstance(result, dict)
