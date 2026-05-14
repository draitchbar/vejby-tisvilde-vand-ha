"""Unit tests for sensor native_value, available, and extra_state_attributes."""
import pytest
from unittest.mock import MagicMock

from vejby_tisvilde_vand.models import CoordinatorData, Device
import vejby_tisvilde_vand.sensor as sensor_module


def _make_sensor(cls, device, coordinator):
    sensor = cls.__new__(cls)
    sensor.coordinator = coordinator
    sensor._device = device
    return sensor


def _make_coordinator(data):
    coord = MagicMock()
    coord.data = data
    coord.last_update_success = True
    return coord


def _make_device(device_id="dev-1"):
    return Device(
        id=device_id,
        location_id="loc-1",
        location_name="Testvej 1",
        device_type="WaterMeter",
    )


# ---------------------------------------------------------------------------
# native_value
# ---------------------------------------------------------------------------

def test_latest_consumption_native_value():
    device = _make_device()
    data = CoordinatorData(latest_usage={"dev-1": 1.5})
    coord = _make_coordinator(data)
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, device, coord)
    assert s.native_value == 1.5


def test_daily_consumption_native_value():
    device = _make_device()
    data = CoordinatorData(daily_usage={"dev-1": 3.0})
    coord = _make_coordinator(data)
    s = _make_sensor(sensor_module.VejbyTisvildeVandDailyConsumptionSensor, device, coord)
    assert s.native_value == 3.0


def test_native_value_none_when_no_data():
    device = _make_device()
    coord = _make_coordinator(None)
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, device, coord)
    assert s.native_value is None


def test_native_value_none_when_device_missing_from_usage():
    device = _make_device("dev-99")
    data = CoordinatorData(latest_usage={"dev-1": 1.0})
    coord = _make_coordinator(data)
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, device, coord)
    assert s.native_value is None


# ---------------------------------------------------------------------------
# available
# ---------------------------------------------------------------------------

def test_available_true_when_data_present():
    coord = _make_coordinator(CoordinatorData())
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, _make_device(), coord)
    assert s.available is True


def test_available_false_when_data_none():
    coord = _make_coordinator(None)
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, _make_device(), coord)
    assert s.available is False


def test_available_false_when_last_update_failed():
    coord = _make_coordinator(CoordinatorData())
    coord.last_update_success = False
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, _make_device(), coord)
    assert s.available is False


# ---------------------------------------------------------------------------
# extra_state_attributes
# ---------------------------------------------------------------------------

def test_extra_state_attributes():
    device = _make_device()
    coord = _make_coordinator(CoordinatorData())
    s = _make_sensor(sensor_module.VejbyTisvildeVandLatestConsumptionSensor, device, coord)
    attrs = s.extra_state_attributes
    assert attrs["device_id"] == "dev-1"
    assert attrs["location"] == "Testvej 1"
    assert attrs["device_type"] == "WaterMeter"
