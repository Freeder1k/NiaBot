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


async def stats(guild: str) -> Stats | None:
    """
    Guild information, such as: level, members, territories, xp, and more.
    :param guild: The name of the guild (case-sensitive and can't be the tag).
    """
    res = await wynnAPI.get_legacy("guildStats", guild)
    if res is None:
        return None
    return utils.misc.dataclass_from_dict(Stats, res)
