import logging
import json
import requests
import voluptuous as vol

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODES,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    AILINK_API_URL,
    CONF_USERID,
    CONF_ACCESSTOKEN,
    CONF_FAMILYID,
    SERVICE_IDENTIFIER,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType = None,
):
    """Set up the Ao Smith Water Heater climate platform."""
    if discovery_info is None:
        return

    data = hass.data[DOMAIN]
    userid = data["userid"]
    accesstoken = data["accesstoken"]
    familyid = data["familyid"]
    name = data["name"]

    async_add_entities([AOSmithWaterHeater(userid, accesstoken, familyid, name)])


class AOSmithWaterHeater(ClimateEntity):
    """Representation of an Ao Smith Water Heater."""

    def __init__(self, userid, accesstoken, familyid, name):
        """Initialize the climate device."""
        self._userid = userid
        self._accesstoken = accesstoken
        self._familyid = familyid
        self._name = name or DEFAULT_NAME
        self._state = HVAC_MODE_OFF  # Initialize as off
        self._support_flags = SUPPORT_TARGET_TEMPERATURE
        self._temperature = None  # You might need a way to fetch the current temperature
        self._device_id = "YOUR_DEVICE_ID" # Replace with your device ID.  Potentially retrieve this via an initial API call if needed.
        self._product_type = "21" #DR1600HF1
        self._device_type = "DR1600HF1"

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._userid}_aosmith_waterheater"

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

    @property
    def hvac_mode(self):
        """Return current operation."""
        return self._state

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes."""
        return [HVAC_MODE_OFF, HVAC_MODE_HEAT]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature # Needs implementation to fetch actual temperature

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug(f"Setting HVAC mode to: {hvac_mode}")
        if hvac_mode == HVAC_MODE_HEAT:
            await self._set_heater_state(1)  # Turn on
            self._state = HVAC_MODE_HEAT
        elif hvac_mode == HVAC_MODE_OFF:
            await self._set_heater_state(0)  # Turn off
            self._state = HVAC_MODE_OFF
        else:
            _LOGGER.warning(f"Unsupported HVAC mode: {hvac_mode}")
            return

        self.async_write_ha_state()

    async def _set_heater_state(self, command_value):
        """Send the request to Ao Smith API to set the heater state."""
        headers = {
            "Host": "ailink-api.hotwater.com.cn",
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"Bearer {self._accesstoken}",
            "Userid": self._userid,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://ailink-appservice-h5-prd.hotwater.com.cn",
            "Referer": "https://ailink-appservice-h5-prd.hotwater.com.cn/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        payload = {
            "userId": self._userid,
            "familyId": self._familyid,
            "appSource": 2,
            "commandSource": 1,
            "invokeTime": "2024-08-11 11:20:03",  # Consider generating a dynamic timestamp here
            "payLoad": json.dumps({
                "profile": {
                    "deviceId": self._device_id,
                    "productType": self._product_type,
                    "deviceType": self._device_type
                },
                "service": {
                    "identifier": SERVICE_IDENTIFIER,
                    "inputData": {"CommandValue": str(command_value)}
                }
            })
        }

        try:
            response = await self.hass.async_add_executor_job(
                requests.post, AILINK_API_URL, headers=headers, json=payload, timeout=10
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            _LOGGER.debug(f"API Response: {response.text}")

            # Consider handling the response to confirm success
            response_json = response.json()
            if response_json.get("code") != "200":
                _LOGGER.error(f"Error from API: {response_json.get('msg')}")
            else:
                _LOGGER.info(f"Successfully set heater state to {command_value}")


        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error calling API: {e}")


    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._temperature

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._temperature = temperature
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the water heater.  Implement actual data fetching here."""
        _LOGGER.debug("Running update...")
        # In a real implementation, you would fetch the current state (temperature, on/off status)
        # from the Ao Smith API. For example:
        # await self._update_from_api()

        # Example only.  Replace with actual data fetching.
        # self._temperature = 65  # Update with actual temperature
        # self._state = HVAC_MODE_HEAT if ... else HVAC_MODE_OFF # Update based on API
        # await self.async_write_ha_state()
        pass
