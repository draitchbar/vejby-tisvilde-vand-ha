"""The Vejby Tisvilde Vand integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VejbyTisvildeVandApi, VejbyTisvildeVandApiError, VejbyTisvildeVandAuthError
from .const import DOMAIN, UPDATE_INTERVAL
from .date_ranges import TimezoneAwareDateRangeProvider
from .http_client import AioHttpClient
from .models import CoordinatorData, Device

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vejby Tisvilde Vand from a config entry."""
    session = async_get_clientsession(hass)
    timezone = str(hass.config.time_zone)

    api = VejbyTisvildeVandApi(
        AioHttpClient(session),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        TimezoneAwareDateRangeProvider(timezone),
    )

    try:
        await api.authenticate()
    except VejbyTisvildeVandAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        return False
    except VejbyTisvildeVandApiError as err:
        _LOGGER.error("API error during setup: %s", err)
        return False

    coordinator = VejbyTisvildeVandDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _parse_devices(customer_data: dict) -> list[Device]:
    """Extract Device objects from raw customer API response."""
    devices = []
    for location in customer_data.get("Locations", []):
        location_id = location.get("LocationId")
        location_name = location.get("Address", "Unknown Address")
        for raw in location.get("Devices", []):
            device_id = raw.get("Id")
            if device_id:
                devices.append(Device(
                    id=device_id,
                    location_id=location_id,
                    location_name=location_name,
                    device_type=raw.get("DeviceType", "WaterMeter"),
                ))
    return devices


class VejbyTisvildeVandDataUpdateCoordinator(DataUpdateCoordinator[CoordinatorData]):
    """Class to manage fetching Vejby Tisvilde Vand data."""

    def __init__(self, hass: HomeAssistant, api: VejbyTisvildeVandApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from API."""
        try:
            customer_data = await self.api.get_customer_details(include_disabled_devices=False)
            devices = _parse_devices(customer_data)

            if not devices:
                _LOGGER.warning("No devices found for customer")
                return CoordinatorData()

            devices_by_location: dict[str, list[str]] = {}
            for device in devices:
                devices_by_location.setdefault(device.location_id, []).append(device.id)

            daily_usage: dict[str, float] = {}
            yesterday_usage: dict[str, float] = {}
            monthly_usage: dict[str, float] = {}
            yearly_usage: dict[str, float] = {}

            for loc_id, loc_device_ids in devices_by_location.items():
                daily_usage.update(await self.api.get_daily_usage(loc_id, loc_device_ids))
                yesterday_usage.update(await self.api.get_yesterday_usage(loc_id, loc_device_ids))
                monthly_usage.update(await self.api.get_monthly_usage(loc_id, loc_device_ids))
                yearly_usage.update(await self.api.get_yearly_usage(loc_id, loc_device_ids))

            return CoordinatorData(
                devices=devices,
                daily_usage=daily_usage,
                yesterday_usage=yesterday_usage,
                monthly_usage=monthly_usage,
                yearly_usage=yearly_usage,
            )

        except VejbyTisvildeVandAuthError as err:
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except VejbyTisvildeVandApiError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
