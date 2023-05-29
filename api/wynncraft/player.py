from dataclasses import dataclass
from typing import Any

import util
from . import wynnAPI
from .. import rateLimit

player_rate_limit = rateLimit.RateLimit(750, 30)
rateLimit.add_ratelimit(player_rate_limit)


@dataclass(frozen=True)
class Stats:
    @dataclass(frozen=True)
    class Meta:
        @dataclass(frozen=True)
        class Location:
            online: bool
            server: str

        @dataclass(frozen=True)
        class Tag:
            display: bool
            value: str

        firstJoin: str
        lastJoin: str
        location: Location
        playtime: int
        tag: Tag
        veteran: bool

    @dataclass(frozen=True)
    class Guild:
        name: str
        rank: str

    username: str
    uuid: str
    rank: str
    meta: Meta
    characters: Any
    guild: Guild
    global_stats: Any
    ranking: Any


async def stats(player: str) -> Stats | None:
    with player_rate_limit:
        json = await wynnAPI.get_v2(f"/player/{player}/stats")

        if len(json) == 0:
            return None

        json = json[0]

        json["global_stats"] = json.pop("global")
        return util.from_dict(Stats, json)
