from dataclasses import dataclass

from async_lru import alru_cache

from . import sessionManager, rateLimit

_athena_rate_limit = rateLimit.RateLimit(20, 1)

_athena_api_session_id = sessionManager.register_session("https://athena.wynntils.com/")


@dataclass(frozen=True)
class Guild:
    name: str
    prefix: str
    color: str = None


@alru_cache(ttl=600)
async def get_guilds() -> list[Guild]:
    session = sessionManager.get_session(_athena_api_session_id)
    with _athena_rate_limit:
        async with session.get("/cache/get/guildList") as resp:
            resp.raise_for_status()

            json = await resp.json()

            return [Guild(g["_id"], g["prefix"], g.get("color", None)) for g in json]


@alru_cache(ttl=600)
async def get_guild_color(name: str) -> str | None:
    guilds = await get_guilds()
    for g in guilds:
        if g.name == name:
            return g.color

    return None
