import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .switch import AOSmithHeaterSwitch

_LOGGER = logging.getLogger(__name__)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the AO Smith Water Heater platform."""
    required_keys = ['access_token', 'user_id', 'family_id', 'device_id', 'product_type', 'device_type']
    if not all(key in config for key in required_keys):
        _LOGGER.error("Missing required configuration parameters")
        return

    add_entities([AOSmithHeaterSwitch(config)])
