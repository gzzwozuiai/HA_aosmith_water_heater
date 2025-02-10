import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import (
    DOMAIN,
    CONF_USERID,
    CONF_ACCESSTOKEN,
    CONF_FAMILYID,
    DEFAULT_NAME
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERID): cv.string,
                vol.Required(CONF_ACCESSTOKEN): cv.string,
                vol.Required(CONF_FAMILYID): cv.string,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ao Smith Water Heater component."""
    conf = config[DOMAIN]
    userid = conf.get(CONF_USERID)
    accesstoken = conf.get(CONF_ACCESSTOKEN)
    familyid = conf.get(CONF_FAMILYID)
    name = conf.get(CONF_NAME)

    hass.data[DOMAIN] = {
        "userid": userid,
        "accesstoken": accesstoken,
        "familyid": familyid,
        "name": name,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config, "climate")
    )

    return True
