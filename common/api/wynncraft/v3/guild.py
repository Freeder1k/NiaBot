import aiohttp
from async_lru import alru_cache

from common.api.wynncraft.v3 import session
from common.types.wynncraft import GuildStats, Territory, WynncraftGuild


@alru_cache(maxsize=None, ttl=600)
async def stats(*, name: str = None, tag: str = None) -> GuildStats:
    """
    Get guild stats by either the tag or name. Exactly one of the arguments must be provided.

    :param name: The name of the guild.
    :param tag: The tag of the guild.
    :returns: A :obj:`GuildStats` object.
    :raises UnknownGuildException: if the guild wasn't found.
    """
    if (name is None) and (tag is not None):
        guild_url = f"/guild/prefix/{tag}"
    elif (name is not None) and (tag is None):
        guild_url = f"/guild/{name}"
    else:
        raise TypeError("Exactly one argument (either name or tag) must be provided.")

    try:
        data = await session.get(guild_url, identifier='uuid')
        return GuildStats.from_json(data)
    except aiohttp.ClientResponseError as e:
        if e.status == 404:
            raise UnknownGuildException(f'Guild with {f"name={name}" if tag is None else f"tag={tag}"} not found.')
        raise e


@alru_cache(ttl=3600)
async def list_guilds() -> list[WynncraftGuild]:
    """
    Request a list of all wynncraft guilds.
    """
    data: dict = await session.get("/guild/list/guild")

    return [WynncraftGuild(name, g['prefix']) for name, g in data.items()]


@alru_cache(ttl=10)
async def list_territories() -> dict[str, Territory]:
    """
    Request a dictionary of information on all territories.
    """
    data: dict = await session.get("/guild/list/territory")

    return {k: Territory.from_json(v) for k, v in data.items()}


@alru_cache(ttl=60)
async def find(s: str) -> tuple[WynncraftGuild]:
    """
    Returns any guilds whose tag or name matches the provided string (case-insensitive).

    :return: A tuple of guilds.
    """
    s = s.lower()
    guilds: list[WynncraftGuild] = await list_guilds()
    return tuple(g for g in guilds if g.name.lower() == s or g.tag.lower() == s)


class UnknownGuildException(Exception):
    pass
