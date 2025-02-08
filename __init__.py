"""The AO Smith integration."""
import logging
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up from config entry."""
    api = AOSmithAPI(hass, entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    return True

class AOSmithAPI:
    """API client for AO Smith."""
    
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.session = aiohttp.ClientSession()

    async def send_command(self, value):
        """Send control command."""
        headers = HEADERS.copy()
        headers.update({
            "Authorization": f"Bearer {self.config['access_token']}",
            "Userid": self.config["user_id"],
            "Familyid": self.config["family_id"]
        })

        payload = {
            "userId": self.config["user_id"],
            "familyId": self.config["family_id"],
            "appSource": 2,
            "commandSource": 1,
            "payLoad": {
                "profile": {
                    "deviceId": self.config["device_id"],
                    "productType": "21",
                    "deviceType": "DR1600HF1"
                },
                "service": {
                    "identifier": SERVICE_SET_HEATER,
                    "inputData": {
                        "CommandValue": str(value)
                    }
                }
            }
        }

        async with self.session.post(
            API_URL,
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                _LOGGER.error("Failed to send command: %s", await response.text())
