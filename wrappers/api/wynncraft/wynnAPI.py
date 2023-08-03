from async_lru import alru_cache

from .. import sessionManager, rateLimit

_legacy_rate_limit = rateLimit.register_new_ratelimit(1200, 20)

_legacy_session_id = sessionManager.register_session("https://api-legacy.wynncraft.com")
_v2_session_id = sessionManager.register_session("https://api.wynncraft.com")


@alru_cache(ttl=59)
async def get_legacy(action: str, command: str = "") -> dict | None:
    """
    Access the legacy wynncraft API. Ratelimiting is handled by this function.
    """
    session = sessionManager.get_session(_legacy_session_id)
    with _legacy_rate_limit:
        async with session.get("/public_api.php", params={"action": action, "command": command}) as resp:
            resp.raise_for_status()

            json = await resp.json()

            if "error" in json:
                return None
            json.pop("request")
            return json


async def get_v2(url: str) -> dict:
    """
    Access the new wynncraft API. Ratelimiting has to be handled by the caller since each endpoint has a different
    ratelimit.
    """
    session = sessionManager.get_session(_v2_session_id)
    async with session.get(f"/v2{url}") as resp:
        resp.raise_for_status()

        json = await resp.json()
        if "data" not in json:
            print(json)
            return {}
        return json["data"]
