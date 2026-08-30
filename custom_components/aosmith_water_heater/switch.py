"""Switch platform for the A.O. Smith water heater integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import AOSmithApiError, AOSmithAuthError
from .const import (
    ATTR_DEBUG_KEYS,
    CONF_HEATER_STATE_KEY,
    DEFAULT_HEATER_STATE_KEY,
)
from .coordinator import AOSmithCoordinator
from .entity import AOSmithEntity

_LOGGER = logging.getLogger(__name__)

# How many polls an unconfirmed command is allowed to hold the optimistic state.
_PENDING_UPDATES = 3


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the heater switch for a config entry."""
    async_add_entities([AOSmithHeaterSwitch(entry.runtime_data, entry)])


class AOSmithHeaterSwitch(AOSmithEntity, SwitchEntity):
    """Controls the heating function via the SetHeaterOnOff command."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "heater"

    def __init__(self, coordinator: AOSmithCoordinator, entry: ConfigEntry) -> None:
        """Initialise the switch and resolve which property mirrors its state."""
        super().__init__(coordinator, "heater")
        self._state_key: str = entry.options.get(
            CONF_HEATER_STATE_KEY, DEFAULT_HEATER_STATE_KEY
        )
        # Set when a command is sent, so the UI does not snap back during the
        # window before the device pushes a fresh property report. Held for at
        # most _PENDING_UPDATES polls so a wrong state key cannot wedge it.
        self._pending: bool | None = None
        self._pending_polls = 0

    @property
    def is_on(self) -> bool | None:
        """Return whether the heating function is on."""
        if self._pending is not None:
            return self._pending
        if (data := self.coordinator.data) is None:
            return None
        value = data.get(self._state_key)
        if value is None:
            return None
        try:
            return bool(int(value))
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the candidate properties so the state key can be identified."""
        if (data := self.coordinator.data) is None:
            return None
        attrs: dict[str, Any] = {"state_key": self._state_key}
        attrs.update(
            {key: data.get(key) for key in ATTR_DEBUG_KEYS if data.get(key) is not None}
        )
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the heating function on."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the heating function off."""
        await self._async_set(False)

    async def _async_set(self, turn_on: bool) -> None:
        """Send the command and only then reflect the new state."""
        try:
            await self.coordinator.client.async_set_heater(turn_on)
        except AOSmithAuthError as err:
            raise ConfigEntryAuthFailed(
                "The A.O. Smith access token has expired"
            ) from err
        except AOSmithApiError as err:
            raise HomeAssistantError(
                f"Failed to switch the heater {'on' if turn_on else 'off'}: {err}"
            ) from err

        self._pending = turn_on
        self._pending_polls = 0
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    def _handle_coordinator_update(self) -> None:
        """Drop the pending state once the device confirms it, or on timeout."""
        if self._pending is not None:
            self._pending_polls += 1
            data = self.coordinator.data
            value = data.get(self._state_key) if data else None
            confirmed = False
            try:
                confirmed = value is not None and bool(int(value)) == self._pending
            except (TypeError, ValueError):
                confirmed = False
            if confirmed or self._pending_polls >= _PENDING_UPDATES:
                if not confirmed:
                    _LOGGER.debug(
                        "Device never reported %s=%s after the command; "
                        "the configured state key may be wrong",
                        self._state_key,
                        int(self._pending),
                    )
                self._pending = None
        super()._handle_coordinator_update()
