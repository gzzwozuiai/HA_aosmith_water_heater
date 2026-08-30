"""Constants for the A.O. Smith water heater integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "aosmith_water_heater"

# Configuration keys owned by this integration. CONF_ACCESS_TOKEN and
# CONF_DEVICE_ID are imported from homeassistant.const where they are needed.
CONF_USER_ID: Final = "user_id"
CONF_FAMILY_ID: Final = "family_id"
CONF_PRODUCT_TYPE: Final = "product_type"
CONF_DEVICE_TYPE: Final = "device_type"
CONF_HEATER_STATE_KEY: Final = "heater_state_key"

DEFAULT_NAME: Final = "A.O. Smith Water Heater"
DEFAULT_PRODUCT_TYPE: Final = "21"
DEFAULT_DEVICE_TYPE: Final = "DR1600HF1"

MANUFACTURER: Final = "A.O. Smith"

API_BASE: Final = "https://ailink-api.hotwater.com.cn/AiLinkService"
API_INVOKE_PATH: Final = "/device/invokeMethod"
API_STATUS_PATH: Final = "/appDevice/getHomepageV2"

SERVICE_SET_HEATER: Final = "SetHeaterOnOff"

SCAN_INTERVAL_SECONDS: Final = 60

# The device reports dozens of properties but does not label which one mirrors
# the SetHeaterOnOff command. These are the plausible candidates; the active one
# is chosen in the options flow. All of them are exposed as attributes on the
# switch so the correct key can be identified by toggling and comparing.
HEATER_STATE_KEY_CANDIDATES: Final = (
    "boiling",
    "heating",
    "powerStatus",
    "warmModel",
    "heatingMachineStatus1",
    "workStatus",
)
DEFAULT_HEATER_STATE_KEY: Final = "boiling"

# Keys from the property report that are surfaced as attributes for debugging.
ATTR_DEBUG_KEYS: Final = HEATER_STATE_KEY_CANDIDATES + (
    "hotWaterTemp",
    "coldWaterTemp",
    "deviceStatus",
    "waterLevelStatus",
    "errorCode",
)
