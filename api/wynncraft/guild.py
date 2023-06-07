from dataclasses import dataclass

import utils.misc
from . import wynnAPI


@dataclass(frozen=True)
class Stats:
    @dataclass(frozen=True)
    class Member:
        name: str
        uuid: str
        rank: str
        contributed: str
        joined: str
        joinedFriendly: str

    @dataclass(frozen=True)
    class Guild:
        name: str
        rank: str

    name: str
    prefix: str
    members: list[Member]
    xp: int
    level: int
    created: str
    createdFriendly: str
    territories: int
    banner: dict


async def guild_list():
    return (await wynnAPI.get_legacy("guildList"))["guilds"]


async def stats(guild: str) -> Stats:
    return utils.misc.dataclass_from_dict(Stats, await wynnAPI.get_legacy("guildStats", guild))
