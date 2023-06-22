import asyncio
import traceback
from queue import Queue

from discord.ext import tasks

import api.minecraft
import api.rateLimit
import api.wynncraft.guild
import api.wynncraft.network
import storage.usernameData
import utils.logging
from dataTypes import MinecraftPlayer

_online_players = set()
_unknown_players = Queue()
_reservation_id = api.minecraft._usernames_rate_limit.reserve(20)
_server_list = []


async def _get_and_store_from_api(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await api.minecraft.get_player(uuid=uuid, username=username)
    if p is not None:
        await storage.usernameData.update(*p)
    return p


# TODO caching
async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    p = await storage.usernameData.get_player(uuid=uuid, username=username)
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

    stored = await storage.usernameData.get_players(uuids=uuids, usernames=usernames)
    known_uuids = {p.uuid for p in stored}
    known_names = {p.name for p in stored}

    unkown_uuids = set(uuids) - known_uuids
    unknown_names = set(usernames) - known_names

    if len(unkown_uuids) + len(unknown_names) > api.minecraft._mojang_rate_limit.get_remaining():
        raise api.rateLimit.RateLimitException("API usage would exceed ratelimit!")

    if len(unkown_uuids) > 0:
        stored += [p for p in (await asyncio.gather(*(_get_and_store_from_api(uuid=uuid) for uuid in unkown_uuids))) if
                   p is not None]
    if len(unknown_names) > 0:
        stored += [p for p in
                   (await asyncio.gather(*(_get_and_store_from_api(username=name) for name in unknown_names))) if
                   p is not None]

    return stored


def get_online_wynncraft_players() -> set[str]:
    return _online_players


async def get_server_list() -> dict[str, list[str]]:
    global _server_list
    if _server_list is None:
        _server_list = await api.wynncraft.network.server_list()

    return _server_list


@tasks.loop(minutes=1, reconnect=True)
async def update_players():
    try:
        global _online_players, _unknown_players, _server_list
        _server_list = await api.wynncraft.network.server_list()
        now_online_players = set().union(*(_server_list.values()))
        new_joins = now_online_players - _online_players
        _online_players = now_online_players

        known_names = {p.name for p in await storage.usernameData.get_players(usernames=list(new_joins))}
        unknown_joined_players = [name for name in new_joins if name not in known_names]
        for i in range(0, len(unknown_joined_players), 10):
            _unknown_players.put(unknown_joined_players[i:i + 10])
        if not _unknown_players.empty():
            utils.logging.dlog(
                f"Updating {sum((len(_unknown_players.queue[i]) for i in range(min(_unknown_players.qsize(), 20))))}"
                f" minecraft usernames.")

        for i in range(0, min(_unknown_players.qsize(), 20)):
            curr_unkn_p = _unknown_players.get()

            res = await api.minecraft.get_players_from_usernames(curr_unkn_p, reservation_id=_reservation_id)
            await asyncio.gather(*(storage.usernameData.update(uuid, name) for uuid, name in res))

            for name in curr_unkn_p:
                if not any(name == t_name for _, t_name in res):
                    utils.logging.dlog(f"{name} not a minecraft name but online on wynncraft!")
        api.minecraft._usernames_rate_limit.free(_reservation_id)
    except Exception as ex:
        traceback.print_exc()
        raise ex


async def update_nia():
    nia = await api.wynncraft.guild.stats("Nerfuria")
    known_uuids = {p.uuid for p in await storage.usernameData.get_players(uuids=[m.uuid for m in nia.members])}
    unknown_uuids = [m.uuid.replace("-", "").lower() for m in nia.members if
                     m.uuid.replace("-", "").lower() not in known_uuids]
    print(list(known_uuids))
    print(unknown_uuids)
    to_update = Queue()

    for i in range(0, len(unknown_uuids), 50):
        to_update.put(unknown_uuids[i:i + 50])
    print(to_update.qsize())
    while not to_update.empty():
        l = to_update.get()
        print(f"Updating {len(l)} Nia members")
        for uuid in l:
            await get_player(uuid=uuid)
        await asyncio.sleep(65)

    print("done updating")
