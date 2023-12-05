from async_lru import alru_cache

import wrappers.api.wynncraft.v3.guild
from niatypes.dataTypes import WynncraftGuild
from wrappers.wynncraft.types import GuildStats


@alru_cache(ttl=60)
async def find_guilds(s: str) -> tuple[WynncraftGuild]:
    """
    Returns any guilds whose tag or name matches the provided string (case-insensitive).

    :return: A tuple of guilds.
    """
    s = s.lower()
    guilds: list[WynncraftGuild] = await wrappers.api.wynncraft.v3.guild.list_guilds()
    return tuple(g for g in guilds if g.name.lower() == s or g.tag.lower() == s)


async def get_guild_stats(*, name: str = None, tag: str = None) -> GuildStats:
    """
    Get guild stats by either the tag or name. Exactly one of the arguments must be provided.

    :param name: The name of the guild.
    :param tag: The tag of the guild.
    :returns: A :obj:`GuildStats` object.
    :raises UnknownGuildException: if the guild wasn't found.
    """
    data = await wrappers.api.wynncraft.v3.guild.stats(guild_name=name, guild_tag=tag)
    if data is None:
        raise UnknownGuildException(f'Guild with guild_name={name}, tag={tag} not found.')

    return GuildStats.from_json(data)


class UnknownGuildException(Exception):
    pass
