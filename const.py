"""Constants for AO Smith integration."""
DOMAIN = "ao_smith"
DEFAULT_NAME = "AO Smith Water Heater"
API_URL = "https://ailink-api.hotwater.com.cn/AiLinkService/device/invokeMethod"

HEADERS = {
    "Sec-Ch-Ua": '"Chromium";v="127", "Not)A;Brand";v="99"',
    "Accept-Language": "zh-CN",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Pragma": "no-cache",
    "Sec-Ch-Ua-Mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "application/json, text/plain, */*",
    "Cache-Control": "no-cache",
    "Version": "V1.0.1",
    "Origin": "https://ailink-appservice-h5-prd.hotwater.com.cn",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Priority": "u=1, i",
    "Connection": "keep-alive"
}

SERVICE_SET_HEATER = "SetHeaterOnOff"
