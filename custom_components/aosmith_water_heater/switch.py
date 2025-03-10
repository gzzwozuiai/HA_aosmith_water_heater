"""开关实体实现"""
from homeassistant.components.switch import SwitchEntity
from .const import (
    DOMAIN, DEFAULT_NAME,
    DEFAULT_DEVICE_ID, DEFAULT_PRODUCT_TYPE, DEFAULT_DEVICE_TYPE
)
from datetime import datetime
import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """设置开关实体"""
    async_add_entities([HotWaterSwitch(config_entry)])
    return True

class HotWaterSwitch(SwitchEntity):
    def __init__(self, config_entry):
        self._config = config_entry.data
        self._state = False
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{DOMAIN}_{self._config[CONF_USER_ID]}"

    @property
    def is_on(self):
        return self._state

    async def async_turn_on(self, **kwargs):
        await self._send_command(1)
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._send_command(0)
        self._state = False
        self.async_write_ha_state()

    async def _send_command(self, value):
        """发送控制命令"""
        headers = {
            "Authorization": f"Bearer {self._config[CONF_ACCESS_TOKEN]}",
            "Userid": self._config[CONF_USER_ID],
            "Familyid": self._config[CONF_FAMILY_ID],
            "Content-Type": "application/json;charset=UTF-8"
        }

        payload = {
            "userId": self._config[CONF_USER_ID],
            "familyId": self._config[CONF_FAMILY_ID],
            "appSource": 2,
            "commandSource": 1,
            "invokeTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "payLoad": {
                "profile": {
                    "deviceId": DEFAULT_DEVICE_ID,
                    "productType": DEFAULT_PRODUCT_TYPE,
                    "deviceType": DEFAULT_DEVICE_TYPE
                },
                "service": {
                    "identifier": "SetHeaterOnOff",
                    "inputData": {"CommandValue": str(value)}
                }
            }
        }

        try:
            session = aiohttp.ClientSession()
            async with session.post(
                "https://ailink-api.hotwater.com.cn/AiLinkService/device/invokeMethod",
                headers=headers,
                json=payload,
                ssl=True
            ) as response:
                if response.status != 200:
                    _LOGGER.error("API请求失败: %s", await response.text())
        except Exception as e:
            _LOGGER.error("通信错误: %s", str(e))
        finally:
            await session.close()
