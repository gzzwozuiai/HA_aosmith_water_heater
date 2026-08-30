"""Polling coordinator for the A.O. Smith water heater integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AOSmithApiError, AOSmithAuthError, AOSmithClient, DeviceStatus
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class AOSmithCoordinator(DataUpdateCoordinator[DeviceStatus]):
    """Polls the cloud for the device property report."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: AOSmithClient
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> DeviceStatus:
        """Fetch the latest property report."""
        try:
            return await self.client.async_get_status()
        except AOSmithAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except AOSmithApiError as err:
            raise UpdateFailed(str(err)) from err
