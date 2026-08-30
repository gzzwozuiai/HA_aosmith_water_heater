"""Config flow for the A.O. Smith water heater integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import AOSmithApiError, AOSmithAuthError, AOSmithClient, parse_profile
from .const import (
    CONF_DEVICE_TYPE,
    CONF_FAMILY_ID,
    CONF_HEATER_STATE_KEY,
    CONF_PRODUCT_TYPE,
    CONF_USER_ID,
    DEFAULT_HEATER_STATE_KEY,
    DEFAULT_PRODUCT_TYPE,
    DOMAIN,
    HEATER_STATE_KEY_CANDIDATES,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Required(CONF_USER_ID): str,
        vol.Required(CONF_FAMILY_ID): str,
    }
)


def _client(hass: HomeAssistant, data: Mapping[str, Any]) -> AOSmithClient:
    """Build a client for the given credentials."""
    return AOSmithClient(
        async_get_clientsession(hass),
        access_token=data[CONF_ACCESS_TOKEN],
        user_id=data[CONF_USER_ID],
        family_id=data[CONF_FAMILY_ID],
        device_id=data.get(CONF_DEVICE_ID, ""),
        product_type=data.get(CONF_PRODUCT_TYPE, DEFAULT_PRODUCT_TYPE),
        device_type=data.get(CONF_DEVICE_TYPE, ""),
    )


class AOSmithConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the UI configuration flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the flow state."""
        self._credentials: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect the credentials captured from the mobile app."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                devices = await _client(self.hass, user_input).async_list_devices()
            except AOSmithAuthError:
                errors["base"] = "invalid_auth"
            except AOSmithApiError:
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    self._credentials = dict(user_input)
                    self._devices = devices
                    return await self.async_step_device()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick which device in the family to control."""
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = next(
                d for d in self._devices if d.get("deviceId") == device_id
            )
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            product_type = str(device.get("deviceCategory") or DEFAULT_PRODUCT_TYPE)
            device_type = parse_profile(device).get("deviceType", "")
            return self.async_create_entry(
                title=device.get("productName") or device_type or device_id,
                data={
                    **self._credentials,
                    CONF_DEVICE_ID: device_id,
                    CONF_PRODUCT_TYPE: product_type,
                    CONF_DEVICE_TYPE: device_type,
                },
            )

        options = [
            SelectOptionDict(
                value=device["deviceId"],
                label=f"{device.get('productName') or 'Device'} "
                f"({parse_profile(device).get("deviceType", "") or device['deviceId']})",
            )
            for device in self._devices
            if device.get("deviceId")
        ]
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=options, mode=SelectSelectorMode.LIST
                        )
                    )
                }
            ),
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start re-authentication when the bearer token expires."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a freshly captured bearer token."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**entry.data, **user_input}
            try:
                await _client(self.hass, data).async_list_devices()
            except AOSmithAuthError:
                errors["base"] = "invalid_auth"
            except AOSmithApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_ACCESS_TOKEN): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return AOSmithOptionsFlow()


class AOSmithOptionsFlow(OptionsFlow):
    """Lets the user pick which reported property mirrors the heater switch."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the property used as the switch state."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_HEATER_STATE_KEY, DEFAULT_HEATER_STATE_KEY
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HEATER_STATE_KEY, default=current
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=list(HEATER_STATE_KEY_CANDIDATES),
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )
