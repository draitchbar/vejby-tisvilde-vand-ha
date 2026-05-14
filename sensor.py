"""Sensor platform for Vejby Tisvilde Vand integration."""
import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import VejbyTisvildeVandDataUpdateCoordinator
from .const import DOMAIN
from .models import CoordinatorData, Device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vejby Tisvilde Vand sensors based on a config entry."""
    coordinator: VejbyTisvildeVandDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    if coordinator.data:
        for device in coordinator.data.devices:
            entities.append(VejbyTisvildeVandLatestConsumptionSensor(coordinator, device, entry))
            entities.append(VejbyTisvildeVandDailyConsumptionSensor(coordinator, device, entry))
            entities.append(VejbyTisvildeVandMonthlyConsumptionSensor(coordinator, device, entry))
            entities.append(VejbyTisvildeVandYearlyConsumptionSensor(coordinator, device, entry))

    async_add_entities(entities)


class VejbyTisvildeVandConsumptionSensor(
    CoordinatorEntity[VejbyTisvildeVandDataUpdateCoordinator], SensorEntity
):
    """Base class for Vejby Tisvilde Vand consumption sensors."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _usage_attr: str
    _name_suffix: str
    _unique_id_suffix: str

    def __init__(
        self,
        coordinator: VejbyTisvildeVandDataUpdateCoordinator,
        device: Device,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{entry.entry_id}_{device.id}_{self._unique_id_suffix}"

        prefix = f"{device.location_name} Water Meter" if device.location_name else "Water Meter"
        self._attr_name = f"{prefix} {self._name_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.id)},
            "name": prefix,
            "manufacturer": "Vejby Tisvilde Vand",
            "model": device.device_type,
        }

    @property
    def native_value(self) -> float | None:
        data: CoordinatorData | None = self.coordinator.data
        if data is None:
            return None
        usage = getattr(data, self._usage_attr, {}).get(self._device.id)
        if usage is None:
            return None
        return float(usage)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "device_id": self._device.id,
            "location": self._device.location_name,
            "device_type": self._device.device_type,
        }


class VejbyTisvildeVandLatestConsumptionSensor(VejbyTisvildeVandConsumptionSensor):
    """Today's consumption from midnight until now."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _usage_attr = "latest_usage"
    _name_suffix = "Latest Consumption"
    _unique_id_suffix = "latest_consumption"


class VejbyTisvildeVandDailyConsumptionSensor(VejbyTisvildeVandConsumptionSensor):
    """Yesterday's total consumption."""

    _attr_state_class = SensorStateClass.TOTAL
    _usage_attr = "daily_usage"
    _name_suffix = "Daily Consumption"
    _unique_id_suffix = "daily_consumption"

    @property
    def last_reset(self) -> datetime:
        return dt_util.start_of_local_day()


class VejbyTisvildeVandMonthlyConsumptionSensor(VejbyTisvildeVandConsumptionSensor):
    """Month-to-date consumption."""

    _attr_state_class = SensorStateClass.TOTAL
    _usage_attr = "monthly_usage"
    _name_suffix = "Monthly Consumption"
    _unique_id_suffix = "monthly_consumption"

    @property
    def last_reset(self) -> datetime:
        now = dt_util.now()
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class VejbyTisvildeVandYearlyConsumptionSensor(VejbyTisvildeVandConsumptionSensor):
    """Year-to-date consumption."""

    _attr_state_class = SensorStateClass.TOTAL
    _usage_attr = "yearly_usage"
    _name_suffix = "Yearly Consumption"
    _unique_id_suffix = "yearly_consumption"

    @property
    def last_reset(self) -> datetime:
        now = dt_util.now()
        return now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
