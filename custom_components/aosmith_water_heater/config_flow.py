"""配置流程处理"""
from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_ACCESS_TOKEN, CONF_USER_ID, CONF_FAMILY_ID

class HotWaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="HotWater Switch", 
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required(CONF_ACCESS_TOKEN): str,
            vol.Required(CONF_USER_ID): str,
            vol.Required(CONF_FAMILY_ID): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
