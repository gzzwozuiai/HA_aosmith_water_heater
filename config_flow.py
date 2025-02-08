"""Config flow for AO Smith integration."""
import voluptuous as vol
from homeassistant import config_entries

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AO Smith."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(title="AO Smith Water Heater", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("access_token"): str,
                vol.Required("user_id"): str,
                vol.Required("family_id"): str,
                vol.Required("device_id"): str
            }),
            errors=errors
        )
