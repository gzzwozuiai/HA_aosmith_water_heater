"""Sensor platform for the A.O. Smith water heater integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DeviceStatus
from .coordinator import AOSmithCoordinator
from .entity import AOSmithEntity


@dataclass(frozen=True, kw_only=True)
class AOSmithSensorDescription(SensorEntityDescription):
    """Describes an A.O. Smith sensor."""

    value_fn: Callable[[DeviceStatus], float | int | None]
    exists_fn: Callable[[DeviceStatus], bool] = lambda _: True


def _number(status: DeviceStatus, key: str) -> float | int | None:
    """Return a reported property as a number, or None if unusable."""
    value = status.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _filter_description(index: int) -> AOSmithSensorDescription:
    """Build the description for one filter stage."""
    return AOSmithSensorDescription(
        key=f"filter_life_{index}",
        translation_key="filter_life",
        translation_placeholders={"index": str(index)},
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s, i=index: _number(s, f"filterLifetime{i}"),
        # filterGrade reports how many stages this model actually has.
        exists_fn=lambda s, i=index: i <= (_number(s, "filterGrade") or 0),
    )


SENSORS: tuple[AOSmithSensorDescription, ...] = (
    AOSmithSensorDescription(
        key="hot_water_temperature",
        translation_key="hot_water_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: _number(s, "hotWaterTemp"),
    ),
    AOSmithSensorDescription(
        key="water_used_today",
        translation_key="water_used_today",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda s: _number(s, "waterDayUse"),
    ),
    AOSmithSensorDescription(
        key="tds",
        translation_key="tds",
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: _number(s, "nowTDS"),
        # supTds is 0 on models without a TDS probe.
        exists_fn=lambda s: bool(_number(s, "supTds")),
    ),
    *(_filter_description(i) for i in (1, 2, 3, 4)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors reported by the device."""
    coordinator: AOSmithCoordinator = entry.runtime_data
    status = coordinator.data
    async_add_entities(
        AOSmithSensor(coordinator, description)
        for description in SENSORS
        if status is not None and description.exists_fn(status)
    )


class AOSmithSensor(AOSmithEntity, SensorEntity):
    """A single value from the device property report."""

    entity_description: AOSmithSensorDescription

    def __init__(
        self, coordinator: AOSmithCoordinator, description: AOSmithSensorDescription
    ) -> None:
        """Initialise the sensor from its description."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | None:
        """Return the current value."""
        if (data := self.coordinator.data) is None:
            return None
        return self.entity_description.value_fn(data)
