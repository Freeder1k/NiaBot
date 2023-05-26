from dataclasses import dataclass

import util
from . import wynnAPI


@dataclass
class Stats:
    @dataclass
    class Member:
        name: str
        uuid: str
        rank: str
        contributed: str
        joined: str
        joinedFriendly: str

    @dataclass
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
    return util.from_dict(Stats, await wynnAPI.get_legacy("guildStats", guild))
