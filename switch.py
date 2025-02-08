import logging
import aiohttp
import datetime
import time
import json

from homeassistant.components.switch import SwitchEntity
from .const import API_URL, BASE_HEADERS

_LOGGER = logging.getLogger(__name__)

class AOSmithHeaterSwitch(SwitchEntity):
    def __init__(self, config):
        self._config = config
        self._is_on = False
        self._attr_name = "AO Smith Heater"
        self._attr_unique_id = f"aosmith_heater_{config['device_id']}"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        await self._send_command(True)

    async def async_turn_off(self, **kwargs):
        await self._send_command(False)

    async def _send_command(self, state):
        headers = BASE_HEADERS.copy()
        headers.update({
            "Authorization": f"Bearer {self._config['access_token']}",
            "Userid": self._config['user_id'],
            "Familyid": self._config['family_id'],
            "Traceid": self._generate_traceid(),
        })

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        command_value = "1" if state else "0"

        payload = {
            "userId": self._config['user_id'],
            "familyId": self._config['family_id'],
            "appSource": 2,
            "commandSource": 1,
            "invokeTime": current_time,
            "payLoad": json.dumps({
                "profile": {
                    "deviceId": self._config['device_id'],
                    "productType": self._config['product_type'],
                    "deviceType": self._config['device_type']
                },
                "service": {
                    "identifier": "SetHeaterOnOff",
                    "inputData": {
                        "CommandValue": command_value
                    }
                }
            })
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers=headers, json=payload) as response:
                    if response.status == 200:
                        self._is_on = state
                        self.async_write_ha_state()
                        _LOGGER.info("Switch state updated to %s", state)
                    else:
                        response_text = await response.text()
                        _LOGGER.error("API request failed: %s", response_text)
        except Exception as e:
            _LOGGER.error("Error communicating with API: %s", str(e))

    def _generate_traceid(self):
        timestamp = int(time.time() * 1000)
        return f"{timestamp}-67009-0-03"
