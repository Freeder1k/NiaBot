import asyncio

from async_lru import alru_cache

import common.api.minecraft
import common.api.rateLimit
import common.storage.usernameData
from common.types.dataTypes import MinecraftPlayer


async def _get_and_store_from_api(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await common.api.minecraft.get_player(uuid=uuid, username=username)
    if p is not None:
        await common.storage.usernameData.update(*p)
    return p


@alru_cache(ttl=60)
async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await common.storage.usernameData.get_player(uuid=uuid, username=username)
    if p is not None:
        return p

    return await _get_and_store_from_api(uuid=uuid, username=username)


# TODO improve
async def get_players(*, uuids: list[str] = None, usernames: list[str] = None) -> list[MinecraftPlayer]:
    """
    Get a list of players by uuids and names.

    :return: A list containing all players that were found.
    """
    if uuids is None:
        uuids = []
    if usernames is None or len(usernames) == 0:
        usernames = []

    uuids = [uuid.replace("-", "").lower() for uuid in uuids]

    stored = await common.storage.usernameData.get_players(uuids=uuids, usernames=usernames)
    known_uuids = {p.uuid for p in stored}
    known_names = {p.name for p in stored}

    unkown_uuids = set(uuids) - known_uuids
    unknown_names = set(usernames) - known_names

    if len(unkown_uuids) + len(unknown_names) > common.api.minecraft._mojang_rate_limit.calculate_remaining_calls():
        raise common.api.rateLimit.RateLimitException("API usage would exceed ratelimit!")

    if len(unkown_uuids) > 0:
        stored += [p for p in (await asyncio.gather(*(_get_and_store_from_api(uuid=uuid) for uuid in unkown_uuids))) if
                   p is not None]
    if len(unknown_names) > 0:
        stored += [p for p in
                   (await asyncio.gather(*(_get_and_store_from_api(username=name) for name in unknown_names))) if
                   p is not None]

    return stored
