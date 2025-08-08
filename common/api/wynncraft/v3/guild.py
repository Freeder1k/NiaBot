import aiohttp
from async_lru import alru_cache

from common.api.wynncraft.v3 import session
from common.api.wynncraft.v3.wynnRateLimit import WynnRateLimit
from common.types.wynncraft import GuildStats, Territory, WynncraftGuild

_guild_rate_limit = WynnRateLimit()


def _switch_uuid_and_name(data):
    new_members_dict = {}
    for rank, rank_members in data["members"].items():
        if not isinstance(rank_members, dict):
            new_members_dict[rank] = rank_members
            continue
        new_members_dict[rank] = {}
        for name, member_stats in rank_members.items():
            uuid = member_stats["uuid"]
            if isinstance(member_stats, dict) and "uuid" in member_stats:
                new_members_dict[rank][uuid] = member_stats
                new_members_dict[rank][uuid]["username"] = name

    data["members"] = new_members_dict


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
        data = await session.get(guild_url, rate_limit=_guild_rate_limit)
        _switch_uuid_and_name(data)
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
    data: dict = await session.get("/guild/list/guild", rate_limit=_guild_rate_limit)

    return [WynncraftGuild(name, g['prefix']) for name, g in data.items() if name != "" and g['prefix'] is not None]


@alru_cache(ttl=10)
async def list_territories() -> dict[str, Territory]:
    """
    Request a dictionary of information on all territories.
    """
    data: dict = await session.get("/guild/list/territory", rate_limit=_guild_rate_limit)

    return {k: Territory.from_json(v) for k, v in data.items()}


def _match(g, s):
    return g.name.lower() == s or g.tag.lower() == s


@alru_cache(ttl=60)
async def find(s: str) -> tuple[WynncraftGuild]:
    """
    Returns any guilds whose tag or name matches the provided string (case-insensitive).

    :return: A tuple of guilds.
    """
    s = s.lower()
    guilds: list[WynncraftGuild] = await list_guilds()
    return tuple(g for g in guilds if _match(g, s))


class UnknownGuildException(Exception):
    pass

def calculate_remaining_requests():
    return _guild_rate_limit.calculate_remaining_calls()


def ratelimit_reset_time():
    return _guild_rate_limit.get_time_until_reset()
