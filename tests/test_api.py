"""Unit tests for VejbyTisvildeVandApi."""
import pytest
from unittest.mock import AsyncMock

from helpers import SAMPLE_CUSTOMER_DATA, SAMPLE_USAGE_RESPONSE, MockHttpClient, MockDateRangeProvider
from vejby_tisvilde_vand.api import VejbyTisvildeVandApi, VejbyTisvildeVandAuthError, VejbyTisvildeVandApiError
from vejby_tisvilde_vand.http_client import HttpError


def make_api(http=None, date_ranges=None):
    return VejbyTisvildeVandApi(
        http or MockHttpClient(),
        "test@example.com",
        "secret",
        date_ranges or MockDateRangeProvider(),
    )


# ---------------------------------------------------------------------------
# authenticate()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_authenticate_stores_token():
    http = MockHttpClient()
    http.post.return_value = {"AuthToken": "tok-123"}
    api = make_api(http)
    await api.authenticate()
    assert api._token == "tok-123"


@pytest.mark.asyncio
async def test_authenticate_raises_auth_error_on_401():
    http = MockHttpClient()
    http.post.side_effect = HttpError(401, "Unauthorized")
    api = make_api(http)
    with pytest.raises(VejbyTisvildeVandAuthError):
        await api.authenticate()


@pytest.mark.asyncio
async def test_authenticate_raises_api_error_on_500():
    http = MockHttpClient()
    http.post.side_effect = HttpError(500, "Server error")
    api = make_api(http)
    with pytest.raises(VejbyTisvildeVandApiError):
        await api.authenticate()


# ---------------------------------------------------------------------------
# get_customer_details()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_customer_details_returns_data():
    http = MockHttpClient()
    http.post.return_value = {"AuthToken": "tok"}
    http.get.return_value = SAMPLE_CUSTOMER_DATA
    api = make_api(http)
    result = await api.get_customer_details()
    assert result == SAMPLE_CUSTOMER_DATA


@pytest.mark.asyncio
async def test_get_customer_details_retries_on_401():
    http = MockHttpClient()
    http.post.return_value = {"AuthToken": "tok"}
    http.get.side_effect = [HttpError(401, "Expired"), SAMPLE_CUSTOMER_DATA]
    api = make_api(http)
    api._token = "old-tok"
    result = await api.get_customer_details()
    assert result == SAMPLE_CUSTOMER_DATA
    assert http.post.call_count == 1  # re-auth


# ---------------------------------------------------------------------------
# _parse_total_usage()
# ---------------------------------------------------------------------------

def test_parse_total_usage_extracts_value():
    api = make_api()
    result = api._parse_total_usage({"TotalUsage": 3.14}, ["dev-1"])
    assert result == {"dev-1": 3.14}


def test_parse_total_usage_returns_zero_when_none():
    api = make_api()
    result = api._parse_total_usage({"TotalUsage": None}, ["dev-1"])
    assert result == {"dev-1": 0.0}


def test_parse_total_usage_empty_device_ids():
    api = make_api()
    assert api._parse_total_usage({"TotalUsage": 1.0}, []) == {}


# ---------------------------------------------------------------------------
# get_daily/yesterday/monthly/yearly_usage()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_latest_usage_uses_today_range():
    http = MockHttpClient()
    http.post.side_effect = [{"AuthToken": "tok"}, SAMPLE_USAGE_RESPONSE]
    api = make_api(http)
    result = await api.get_latest_usage("loc-1", ["dev-1"])
    assert result == {"dev-1": 2.5}


@pytest.mark.asyncio
async def test_get_daily_usage():
    http = MockHttpClient()
    http.post.side_effect = [{"AuthToken": "tok"}, SAMPLE_USAGE_RESPONSE]
    api = make_api(http)
    result = await api.get_daily_usage("loc-1", ["dev-1"])
    assert result == {"dev-1": 2.5}


@pytest.mark.asyncio
async def test_get_monthly_usage():
    http = MockHttpClient()
    http.post.side_effect = [{"AuthToken": "tok"}, SAMPLE_USAGE_RESPONSE]
    api = make_api(http)
    result = await api.get_monthly_usage("loc-1", ["dev-1"])
    assert result == {"dev-1": 2.5}


@pytest.mark.asyncio
async def test_get_yearly_usage():
    http = MockHttpClient()
    http.post.side_effect = [{"AuthToken": "tok"}, SAMPLE_USAGE_RESPONSE]
    api = make_api(http)
    result = await api.get_yearly_usage("loc-1", ["dev-1"])
    assert result == {"dev-1": 2.5}
