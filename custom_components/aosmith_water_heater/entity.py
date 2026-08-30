"""Shared entity base for the A.O. Smith water heater integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AOSmithCoordinator
from .const import DOMAIN, MANUFACTURER


class AOSmithEntity(CoordinatorEntity[AOSmithCoordinator]):
    """Base entity tied to the single configured device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AOSmithCoordinator, key: str) -> None:
        """Initialise shared identity and device registry information."""
        super().__init__(coordinator)
        device_id = coordinator.client.device_id
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=MANUFACTURER,
            model=coordinator.client.device_type,
            name=coordinator.data.product_name if coordinator.data else None,
            sw_version=coordinator.data.sw_version if coordinator.data else None,
            serial_number=device_id,
        )

    @property
    def available(self) -> bool:
        """Return whether the cloud reports the device as reachable."""
        return super().available and bool(
            self.coordinator.data and self.coordinator.data.online
        )
