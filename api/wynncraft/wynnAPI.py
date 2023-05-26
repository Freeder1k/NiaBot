import aiohttp

from api import rateLimit

legacy_rate_limit = rateLimit.RateLimit(1200, 20)
rateLimit.add_ratelimit(legacy_rate_limit)

_legacy_session = aiohttp.ClientSession("https://api-legacy.wynncraft.com/public_api.php")
_v2_session = aiohttp.ClientSession("https://api.wynncraft.com/v2")


async def get_legacy(action: str, command: str = ""):
    """
    Access the legacy wynncraft API. Ratelimiting is handled by this function.
    """
    with legacy_rate_limit:
        async with _legacy_session.get("", params={"action": action, "command": command}) as resp:
            json = await resp.json()
            json.pop("request")
            return json


async def get_v2(url: str):
    """
    Access the new wynncraft API. Ratelimiting has to be handled by the caller since each endpoint has a different
    ratelimit.
    """
    async with _v2_session.get(url) as resp:
        return await resp.json()


async def close():
    await _legacy_session.close()
    await _v2_session.close()
