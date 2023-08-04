from dataclasses import dataclass
from typing import Any

import aiohttp.client_exceptions
from async_lru import alru_cache

import utils.misc
from . import wynnAPI
from handlers import rateLimit

player_rate_limit = rateLimit.RateLimit(750, 30)
rateLimit.register_ratelimit(player_rate_limit)


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


@alru_cache(ttl=59)
async def stats(player: str) -> Stats | None:
    """
    Returns a Stats Object, which details public statistical information about the player.
    :param player: Either the username or the uuid in dashed form (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    with player_rate_limit:
        try:
            json = await wynnAPI.get_v2(f"/player/{player}/stats")
        except aiohttp.client_exceptions.ClientResponseError as ex:
            if ex.status == 400:
                return None
            raise ex

        if len(json) == 0:
            return None

        json = json[0]

        json["global_stats"] = json.pop("global")
        json["meta"]["playtime"] = int(json["meta"]["playtime"] * 4.7)
        return utils.misc.dataclass_from_dict(Stats, json)
