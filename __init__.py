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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Vejby Tisvilde Vand from a config entry."""
    session = async_get_clientsession(hass)
    api = VejbyTisvildeVandApi(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
    )

    # Authenticate on setup
    try:
        await api.authenticate()
    except VejbyTisvildeVandAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        return False
    except VejbyTisvildeVandApiError as err:
        _LOGGER.error("API error during setup: %s", err)
        return False

    coordinator = VejbyTisvildeVandDataUpdateCoordinator(hass, api)

    # Fetch initial data
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


class VejbyTisvildeVandDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Vejby Tisvilde Vand data."""

    def __init__(self, hass: HomeAssistant, api: VejbyTisvildeVandApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.api = api
        self.customer_data = None
        self.device_ids = []

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Get customer details including devices
            self.customer_data = await self.api.get_customer_details(
                include_disabled_devices=False
            )

            # Extract device IDs from customer data
            # API uses capitalized keys
            devices = []
            locations = self.customer_data.get("Locations", [])

            for location in locations:
                location_devices = location.get("Devices", [])
                for device in location_devices:
                    device_id = device.get("Id")
                    if device_id:
                        devices.append({
                            "id": device_id,
                            "location_name": location.get("Address", "Unknown Address"),
                            "type": device.get("DeviceType", "WaterMeter"),
                        })

            self.device_ids = [device["id"] for device in devices]

            if not self.device_ids:
                _LOGGER.warning("No devices found for customer")
                return {"devices": [], "daily_usage": {}}

            # Get usage data for all devices
            daily_usage = await self.api.get_daily_usage(self.device_ids)
            monthly_usage = await self.api.get_monthly_usage(self.device_ids)
            yearly_usage = await self.api.get_yearly_usage(self.device_ids)

            # Note: We skip get_latest_readings() as it's not needed for consumption sensors
            # and may require different parameters than the usage endpoint

            return {
                "devices": devices,
                "daily_usage": daily_usage,
                "monthly_usage": monthly_usage,
                "yearly_usage": yearly_usage,
                "customer_data": self.customer_data,
            }

        except VejbyTisvildeVandAuthError as err:
            # Trigger a reauth flow
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except VejbyTisvildeVandApiError as err:
            _LOGGER.error("Error communicating with API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
