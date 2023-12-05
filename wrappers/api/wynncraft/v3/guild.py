import aiohttp
from async_lru import alru_cache

from niatypes.dataTypes import WynncraftGuild
from niatypes.jsonable import JsonType
from wrappers.api.wynncraft.v3 import session
from wrappers.wynncraft.types import Territory


@alru_cache(maxsize=None, ttl=600)
async def stats(*, guild_name: str = None, guild_tag: str = None) -> JsonType | None:
    """
    Request public statistical information about the specified guild. Exactly one of the arguments must be specified.
    :param guild_name: The name of the guild.
    :param guild_tag: The tag of the guild.
    :returns: The api response as a dictionary in JSON format or None, if the guild was not found.
    """
    if (guild_name is None) and (guild_tag is not None):
        guild_url = f"/guild/prefix/{guild_tag}"
    elif (guild_name is not None) and (guild_tag is None):
        guild_url = f"/guild/{guild_name}"
    else:
        raise TypeError("Exactly one argument (either name or tag) must be provided.")

    try:
        return await session.get(guild_url, identifier='uuid')
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            return None
        raise e


@alru_cache(ttl=3600)
async def list_guilds() -> list[WynncraftGuild]:
    """
    Request a list of all wynncraft guilds.
    """
    data: list = await session.get("/guild/list/guild")

    return [WynncraftGuild(g['name'], g['prefix']) for g in data]


@alru_cache(ttl=10)
async def list_territories() -> dict[str, Territory]:
    """
    Request a dictionary of information on all territories.
    """
    data: dict = await session.get("/guild/list/territory")

    return {k: Territory.from_json(v) for k, v in data.items()}
