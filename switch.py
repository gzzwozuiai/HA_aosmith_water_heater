"""Switch platform for AO Smith integration."""
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, API_URL, HEADERS, SERVICE_SET_HEATER

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the AO Smith switch."""
    api = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([AOSmithHeaterSwitch(api)], True)

class AOSmithHeaterSwitch(SwitchEntity):
    """Representation of an AO Smith heater switch."""

    def __init__(self, api):
        """Initialize the switch."""
        self._api = api
        self._is_on = False

    @property
    def name(self):
        """Return the name of the switch."""
        return "AO Smith Heater"

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self._api.send_command(1)
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self._api.send_command(0)
        self._is_on = False

    async def async_update(self):
        """Fetch current state."""
        self._is_on = await self._api.get_current_state()
