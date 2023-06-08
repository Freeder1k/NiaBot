import aiohttp
from aiohttp.client import ClientSession

from api import rateLimit

legacy_rate_limit = rateLimit.RateLimit(1200, 20)
rateLimit.register_ratelimit(legacy_rate_limit)

_legacy_session: ClientSession = None
_v2_session: ClientSession = None


async def get_legacy(action: str, command: str = "") -> dict:
    """
    Access the legacy wynncraft API. Ratelimiting is handled by this function.
    """
    with legacy_rate_limit:
        async with _legacy_session.get("/public_api.php", params={"action": action, "command": command}) as resp:
            resp.raise_for_status()

            json = await resp.json()
            json.pop("request")
            return json


async def get_v2(url: str) -> dict:
    """
    Access the new wynncraft API. Ratelimiting has to be handled by the caller since each endpoint has a different
    ratelimit.
    """
    async with _v2_session.get(f"/v2{url}") as resp:
        resp.raise_for_status()

        json = await resp.json()
        if "data" not in json:
            print(json)
            return {}
        return json["data"]


async def init_sessions():
    global _legacy_session, _v2_session
    _legacy_session = aiohttp.ClientSession("https://api-legacy.wynncraft.com")
    _v2_session = aiohttp.ClientSession("https://api.wynncraft.com")


async def close():
    await _legacy_session.close()
    await _v2_session.close()
