import asyncio

from async_lru import alru_cache

import handlers.rateLimit
import wrappers.api.minecraft
import wrappers.api.wynncraft.network
import wrappers.storage.usernameData
from niatypes.dataTypes import MinecraftPlayer


async def _get_and_store_from_api(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await wrappers.api.minecraft.get_player(uuid=uuid, username=username)
    if p is not None:
        await wrappers.storage.usernameData.update(*p)
    return p


@alru_cache(ttl=60)
async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await wrappers.storage.usernameData.get_player(uuid=uuid, username=username)
    if p is not None:
        return p

    return await _get_and_store_from_api(uuid=uuid, username=username)


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

    stored = await wrappers.storage.usernameData.get_players(uuids=uuids, usernames=usernames)
    known_uuids = {p.uuid for p in stored}
    known_names = {p.name for p in stored}

    unkown_uuids = set(uuids) - known_uuids
    unknown_names = set(usernames) - known_names

    if len(unkown_uuids) + len(unknown_names) > wrappers.api.minecraft._mojang_rate_limit.calculate_remaining_calls():
        raise handlers.rateLimit.RateLimitException("API usage would exceed ratelimit!")

    if len(unkown_uuids) > 0:
        stored += [p for p in (await asyncio.gather(*(_get_and_store_from_api(uuid=uuid) for uuid in unkown_uuids))) if
                   p is not None]
    if len(unknown_names) > 0:
        stored += [p for p in
                   (await asyncio.gather(*(_get_and_store_from_api(username=name) for name in unknown_names))) if
                   p is not None]

    return stored
