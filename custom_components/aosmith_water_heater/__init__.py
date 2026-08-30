"""The A.O. Smith water heater integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AOSmithClient
from .const import (
    CONF_DEVICE_TYPE,
    CONF_FAMILY_ID,
    CONF_PRODUCT_TYPE,
    CONF_USER_ID,
    DEFAULT_DEVICE_TYPE,
    DEFAULT_PRODUCT_TYPE,
)
from .coordinator import AOSmithCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up A.O. Smith water heater from a config entry."""
    client = AOSmithClient(
        async_get_clientsession(hass),
        access_token=entry.data[CONF_ACCESS_TOKEN],
        user_id=entry.data[CONF_USER_ID],
        family_id=entry.data[CONF_FAMILY_ID],
        device_id=entry.data[CONF_DEVICE_ID],
        product_type=entry.data.get(CONF_PRODUCT_TYPE, DEFAULT_PRODUCT_TYPE),
        device_type=entry.data.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE),
    )

    coordinator = AOSmithCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its options changed."""
    await hass.config_entries.async_reload(entry.entry_id)
