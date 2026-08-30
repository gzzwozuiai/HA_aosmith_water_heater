"""Binary sensor platform for the A.O. Smith water heater integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DeviceStatus
from .coordinator import AOSmithCoordinator
from .entity import AOSmithEntity


@dataclass(frozen=True, kw_only=True)
class AOSmithBinarySensorDescription(BinarySensorEntityDescription):
    """Describes an A.O. Smith binary sensor."""

    value_fn: Callable[[DeviceStatus], bool | None]


def _flag(status: DeviceStatus, key: str) -> bool | None:
    """Return a reported property as a boolean, or None if unusable."""
    value = status.get(key)
    if value is None:
        return None
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return None


BINARY_SENSORS: tuple[AOSmithBinarySensorDescription, ...] = (
    AOSmithBinarySensorDescription(
        key="heating",
        translation_key="heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda s: _flag(s, "heating"),
    ),
    AOSmithBinarySensorDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.error_code != 0,
    ),
    AOSmithBinarySensorDescription(
        key="child_lock",
        translation_key="child_lock",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: _flag(s, "childLockStatus"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors reported by the device."""
    coordinator: AOSmithCoordinator = entry.runtime_data
    async_add_entities(
        AOSmithBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class AOSmithBinarySensor(AOSmithEntity, BinarySensorEntity):
    """A single boolean from the device property report."""

    entity_description: AOSmithBinarySensorDescription

    def __init__(
        self,
        coordinator: AOSmithCoordinator,
        description: AOSmithBinarySensorDescription,
    ) -> None:
        """Initialise the binary sensor from its description."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the current state."""
        if (data := self.coordinator.data) is None:
            return None
        return self.entity_description.value_fn(data)
