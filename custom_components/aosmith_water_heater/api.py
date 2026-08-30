"""Async client for the A.O. Smith (AiLink) cloud API."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import (
    API_BASE,
    API_INVOKE_PATH,
    API_STATUS_PATH,
    SERVICE_SET_HEATER,
)

_LOGGER = logging.getLogger(__name__)

# Values the cloud uses for "request succeeded".
_SUCCESS_CODES = {0, 200, "0", "200"}


class AOSmithError(Exception):
    """Base error for this integration."""


class AOSmithAuthError(AOSmithError):
    """The cloud rejected the access token."""


class AOSmithApiError(AOSmithError):
    """The cloud call failed for any other reason."""


class DeviceStatus:
    """A decoded property report for a single device."""

    def __init__(self, device: dict[str, Any], properties: dict[str, Any]) -> None:
        """Wrap the device summary and its decoded property report."""
        self.device = device
        self.properties = properties

    def get(self, key: str, default: Any = None) -> Any:
        """Return a reported property."""
        return self.properties.get(key, default)

    @property
    def product_name(self) -> str | None:
        """Return the human readable product name, e.g. 净水机."""
        return self.device.get("productName")

    @property
    def sw_version(self) -> str | None:
        """Return the reported firmware version."""
        return parse_profile(self.device).get("deviceVersion") or None

    @property
    def online(self) -> bool:
        """Return whether the cloud considers the device reachable."""
        return self.device.get("devState") == 1

    @property
    def error_code(self) -> int:
        """Return the reported fault code, 0 when healthy."""
        try:
            return int(self.properties.get("errorCode", 0))
        except (TypeError, ValueError):
            return 0


class AOSmithClient:
    """Talks to the AiLink cloud on behalf of a single device."""

    def __init__(
        self,
        session: ClientSession,
        *,
        access_token: str,
        user_id: str,
        family_id: str,
        device_id: str,
        product_type: str,
        device_type: str,
    ) -> None:
        """Store the credentials and device identity used for every call."""
        self._session = session
        self._access_token = access_token
        self._user_id = user_id
        self._family_id = family_id
        self._device_id = device_id
        self._product_type = product_type
        self._device_type = device_type

    @property
    def device_id(self) -> str:
        """Return the cloud identifier of the controlled device."""
        return self._device_id

    @property
    def device_type(self) -> str:
        """Return the model string reported to the cloud."""
        return self._device_type

    def set_access_token(self, access_token: str) -> None:
        """Replace the bearer token after a re-authentication."""
        self._access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        # The mobile app also sends Sign/Md5data/Nonce/Timestamp headers, but
        # the gateway does not enforce them on these endpoints.
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Userid": self._user_id,
            "Familyid": self._family_id,
            "Content-Type": "application/json;charset=UTF-8",
        }

    async def _post(self, path: str, body: dict[str, Any]) -> Any:
        """POST a JSON body and return the decoded response."""
        url = f"{API_BASE}{path}"
        try:
            async with self._session.post(
                url, headers=self._headers, json=body
            ) as response:
                text = await response.text()
                if response.status in (401, 403):
                    raise AOSmithAuthError(
                        f"Cloud rejected the access token (HTTP {response.status})"
                    )
                response.raise_for_status()
                try:
                    data = json.loads(text)
                except ValueError as err:
                    raise AOSmithApiError(
                        f"Cloud returned a non-JSON response: {text[:200]}"
                    ) from err
        except ClientResponseError as err:
            raise AOSmithApiError(f"HTTP {err.status} from {url}") from err
        except (ClientError, TimeoutError) as err:
            raise AOSmithApiError(f"Cannot reach {url}: {err}") from err

        if isinstance(data, dict):
            status = data.get("status", data.get("code"))
            if status is not None and status not in _SUCCESS_CODES:
                message = data.get("msg") or data.get("message") or text[:200]
                # An expired token is signalled in the body, not the HTTP status.
                if status in (401, 403, "401", "403"):
                    raise AOSmithAuthError(f"Cloud rejected the token: {message}")
                raise AOSmithApiError(f"Cloud returned status {status}: {message}")

        return data

    async def async_set_heater(self, turn_on: bool) -> None:
        """Turn the heating function on or off."""
        # The cloud expects payLoad as a serialised JSON string, not a nested
        # object. Sending it as an object is accepted by the gateway but fails
        # at dispatch with "下发服务调用失败".
        payload = json.dumps(
            {
                "profile": {
                    "deviceId": self._device_id,
                    "productType": self._product_type,
                    "deviceType": self._device_type,
                },
                "service": {
                    "identifier": SERVICE_SET_HEATER,
                    "inputData": {"CommandValue": "1" if turn_on else "0"},
                },
            },
            separators=(",", ":"),
        )
        await self._post(
            API_INVOKE_PATH,
            {
                "userId": self._user_id,
                "familyId": self._family_id,
                "appSource": 2,
                "commandSource": 1,
                "invokeTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "payLoad": payload,
            },
        )

    async def async_list_devices(self) -> list[dict[str, Any]]:
        """Return every device the family exposes on the app home page."""
        data = await self._post(
            API_STATUS_PATH,
            {
                "homePageVersion": "3",
                "userId": self._user_id,
                "familyId": self._family_id,
            },
        )

        if not isinstance(data, dict):
            raise AOSmithApiError("Unexpected status response shape")

        return (data.get("info") or {}).get("devInfoItemInfoList") or []

    async def async_get_status(self) -> DeviceStatus:
        """Fetch and decode the property report for the configured device."""
        devices = await self.async_list_devices()
        device = next(
            (d for d in devices if d.get("deviceId") == self._device_id), None
        )
        if device is None:
            found = [d.get("deviceId") for d in devices]
            raise AOSmithApiError(
                f"Device {self._device_id} is not in the family; found {found}"
            )

        return DeviceStatus(device, _parse_properties(device))


def _parse_status_info(device: Mapping[str, Any]) -> dict[str, Any]:
    """Decode ``statusInfo``, which is a JSON document embedded as a string."""
    raw = device.get("statusInfo")
    if not raw:
        return {}

    try:
        decoded = json.loads(raw)
    except ValueError:
        _LOGGER.warning("Could not decode statusInfo for %s", device.get("deviceId"))
        return {}

    return decoded if isinstance(decoded, dict) else {}


def parse_profile(device: Mapping[str, Any]) -> dict[str, Any]:
    """Return the firmware/model profile block of a device entry."""
    profile = _parse_status_info(device).get("profile")
    return profile if isinstance(profile, dict) else {}


def _parse_properties(device: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the property report, which lives in the ``post`` event."""
    for event in _parse_status_info(device).get("events") or []:
        if event.get("identifier") == "post":
            output = event.get("outputData")
            if isinstance(output, dict):
                return output

    return {}
