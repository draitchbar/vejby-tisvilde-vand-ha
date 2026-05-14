"""Typed data models for Vejby Tisvilde Vand integration."""
from dataclasses import dataclass, field


@dataclass
class Device:
    """Represents a water meter device."""

    id: str
    location_id: str
    location_name: str
    device_type: str


@dataclass
class CoordinatorData:
    """Data returned by the coordinator on each poll."""

    devices: list[Device] = field(default_factory=list)
    latest_usage: dict[str, float] = field(default_factory=dict)
    daily_usage: dict[str, float] = field(default_factory=dict)
    monthly_usage: dict[str, float] = field(default_factory=dict)
    yearly_usage: dict[str, float] = field(default_factory=dict)
