"""The AO Smith Water Heater integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "aosmith_water_heater"

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the AO Smith Water Heater component."""
    hass.data[DOMAIN] = {}
    return True
