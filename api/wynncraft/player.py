from dataclasses import dataclass

import util
from . import wynnAPI
from .. import rateLimit

player_rate_limit = rateLimit.RateLimit(750, 30)
rateLimit.add_ratelimit(player_rate_limit)


@dataclass
class Stats:
    @dataclass
    class Meta:
        @dataclass
        class Location:
            online: bool
            server: str

        @dataclass
        class Tag:
            display: bool
            value: str

        firstJoin: str
        lastJoin: str
        location: Location
        playtime: int
        tag: Tag
        veteran: bool

    @dataclass
    class Guild:
        name: str
        rank: str

    username: str
    uuid: str
    rank: str
    meta: Meta
    characters: list[dict]
    guild: Guild
    global_stats: dict
    ranking: dict


async def stats(player: str) -> Stats:
    with player_rate_limit:
        json = await wynnAPI.get_v2(f"/player/{player}/stats")
        json["global_stats"] = json.pop("global")
        return util.from_dict(Stats, json['data'][0])
