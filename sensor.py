"""Sensor platform for Vejby Tisvilde Vand integration."""
import logging

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

from . import VejbyTisvildeVandDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vejby Tisvilde Vand sensors based on a config entry."""
    coordinator: VejbyTisvildeVandDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    # Create sensors for each device (daily, monthly, and yearly)
    entities = []

    if coordinator.data and "devices" in coordinator.data:
        for device in coordinator.data["devices"]:
            # Daily consumption sensor
            entities.append(
                VejbyTisvildeVandDailyConsumptionSensor(coordinator, device, entry)
            )
            # Yesterday consumption sensor
            entities.append(
                VejbyTisvildeVandYesterdayConsumptionSensor(coordinator, device, entry)
            )
            # Monthly consumption sensor
            entities.append(
                VejbyTisvildeVandMonthlyConsumptionSensor(coordinator, device, entry)
            )
            # Yearly consumption sensor
            entities.append(
                VejbyTisvildeVandYearlyConsumptionSensor(coordinator, device, entry)
            )

    async_add_entities(entities)


class VejbyTisvildeVandDailyConsumptionSensor(
    CoordinatorEntity[VejbyTisvildeVandDataUpdateCoordinator], SensorEntity
):
    """Representation of a Vejby Tisvilde Vand daily consumption sensor."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(
        self,
        coordinator: VejbyTisvildeVandDataUpdateCoordinator,
        device: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device = device
        self._device_id = device["id"]
        self._attr_unique_id = f"{entry.entry_id}_{self._device_id}_daily_consumption"

        # Set name based on device and location
        location_name = device.get("location_name", "")
        device_name = device.get("name", "Water Meter")

        if location_name:
            self._attr_name = f"{location_name} {device_name} Daily Consumption"
        else:
            self._attr_name = f"{device_name} Daily Consumption"

        # Device info for grouping in UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"{location_name} {device_name}" if location_name else device_name,
            "manufacturer": "Vejby Tisvilde Vand",
            "model": device.get("type", "Water Meter"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        daily_usage = self.coordinator.data.get("daily_usage", {})
        usage = daily_usage.get(self._device_id)

        if usage is None:
            return None

        # API returns cubic meters directly, no conversion needed
        return float(usage) if usage else 0.0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "daily_usage" in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "device_id": self._device_id,
            "location": self._device.get("location_name"),
            "device_type": self._device.get("type"),
        }

        return attributes


class VejbyTisvildeVandYesterdayConsumptionSensor(
    CoordinatorEntity[VejbyTisvildeVandDataUpdateCoordinator], SensorEntity
):
    """Representation of a Vejby Tisvilde Vand yesterday consumption sensor."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(
        self,
        coordinator: VejbyTisvildeVandDataUpdateCoordinator,
        device: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device = device
        self._device_id = device["id"]
        self._attr_unique_id = f"{entry.entry_id}_{self._device_id}_yesterday_consumption"

        # Set name based on device and location
        location_name = device.get("location_name", "")
        device_name = device.get("name", "Water Meter")

        if location_name:
            self._attr_name = f"{location_name} {device_name} Yesterday Consumption"
        else:
            self._attr_name = f"{device_name} Yesterday Consumption"

        # Device info for grouping in UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"{location_name} {device_name}" if location_name else device_name,
            "manufacturer": "Vejby Tisvilde Vand",
            "model": device.get("type", "Water Meter"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        yesterday_usage = self.coordinator.data.get("yesterday_usage", {})
        usage = yesterday_usage.get(self._device_id)

        if usage is None:
            return None

        # API returns cubic meters directly, no conversion needed
        return float(usage) if usage else 0.0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "yesterday_usage" in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "device_id": self._device_id,
            "location": self._device.get("location_name"),
            "device_type": self._device.get("type"),
        }

        return attributes


class VejbyTisvildeVandMonthlyConsumptionSensor(
    CoordinatorEntity[VejbyTisvildeVandDataUpdateCoordinator], SensorEntity
):
    """Representation of a Vejby Tisvilde Vand monthly consumption sensor."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(
        self,
        coordinator: VejbyTisvildeVandDataUpdateCoordinator,
        device: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device = device
        self._device_id = device["id"]
        self._attr_unique_id = f"{entry.entry_id}_{self._device_id}_monthly_consumption"

        # Set name based on device and location
        location_name = device.get("location_name", "")
        device_name = device.get("name", "Water Meter")

        if location_name:
            self._attr_name = f"{location_name} {device_name} Monthly Consumption"
        else:
            self._attr_name = f"{device_name} Monthly Consumption"

        # Device info for grouping in UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"{location_name} {device_name}" if location_name else device_name,
            "manufacturer": "Vejby Tisvilde Vand",
            "model": device.get("type", "Water Meter"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        monthly_usage = self.coordinator.data.get("monthly_usage", {})
        usage = monthly_usage.get(self._device_id)

        if usage is None:
            return None

        # API returns cubic meters directly, no conversion needed
        return float(usage) if usage else 0.0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "monthly_usage" in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "device_id": self._device_id,
            "location": self._device.get("location_name"),
            "device_type": self._device.get("type"),
        }

        return attributes


class VejbyTisvildeVandYearlyConsumptionSensor(
    CoordinatorEntity[VejbyTisvildeVandDataUpdateCoordinator], SensorEntity
):
    """Representation of a Vejby Tisvilde Vand yearly consumption sensor."""

    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS

    def __init__(
        self,
        coordinator: VejbyTisvildeVandDataUpdateCoordinator,
        device: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device = device
        self._device_id = device["id"]
        self._attr_unique_id = f"{entry.entry_id}_{self._device_id}_yearly_consumption"

        # Set name based on device and location
        location_name = device.get("location_name", "")
        device_name = device.get("name", "Water Meter")

        if location_name:
            self._attr_name = f"{location_name} {device_name} Yearly Consumption"
        else:
            self._attr_name = f"{device_name} Yearly Consumption"

        # Device info for grouping in UI
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": f"{location_name} {device_name}" if location_name else device_name,
            "manufacturer": "Vejby Tisvilde Vand",
            "model": device.get("type", "Water Meter"),
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        yearly_usage = self.coordinator.data.get("yearly_usage", {})
        usage = yearly_usage.get(self._device_id)

        if usage is None:
            return None

        # API returns cubic meters directly, no conversion needed
        return float(usage) if usage else 0.0

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "yearly_usage" in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attributes = {
            "device_id": self._device_id,
            "location": self._device.get("location_name"),
            "device_type": self._device.get("type"),
        }

        return attributes
