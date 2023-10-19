from async_lru import alru_cache

from niatypes.dataTypes import WynncraftGuild
from niatypes.wynncraft.v3.guild import GuildStats, Territory
from wrappers.api.wynncraft.v3 import session


class UnknownGuildException(Exception):
    pass


@alru_cache(ttl=600)
async def stats(*, guild_name: str = None, guild_prefix: str = None) -> GuildStats:
    """
    Request public statistical information about the specified guild. Exactly one of the arguments must be specified.
    :param guild_name: The name of the guild.
    :param guild_prefix: The prefix of the guild.
    :returns: A Stats object.
    :raises UnknownGuildException: if the guild wasn't found.
    """
    if (guild_name is None) and (guild_prefix is not None):
        url = f"/guild/prefix/{guild_prefix}"
    elif (guild_name is not None) and (guild_prefix is None):
        url = f"/guild/{guild_name}"
    else:
        raise TypeError("Exactly one argument (either name or prefix) must be provided.")

    data = await session.get(url, identifier='uuid')

    if len(data) == 0 or data['name'] is None:
        raise UnknownGuildException(f'Guild with guild_name={guild_name}, prefix={guild_prefix} not found.')

    return GuildStats.from_json(data)


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
