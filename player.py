import asyncio
from queue import Queue

from discord.ext import tasks

import api.minecraft
import api.wynncraft.network
import storage.usernameData
import utils.logging
from data_types import Player

_online_players = set()
_unknown_players = Queue()
_reservation_id = api.minecraft._usernames_rate_limit.reserve(20)


async def get_player(*, uuid: str = None, username: str = None) -> Player | None:
    if (uuid is None) and (username is not None):
        p = await storage.usernameData.get_player(uuid=uuid, username=username)
        if p is not None:
            return p

        p = await api.minecraft.username_to_player(username)
        if p is not None:
            await storage.usernameData.update(*p)
        return p

    elif (uuid is not None) and (username is None):
        p = await storage.usernameData.get_player(uuid=uuid, username=username)
        if p is not None:
            return p

        p = await api.minecraft.uuid_to_player(uuid)
        if p is not None:
            await storage.usernameData.update(*p)
        return p

    else:
        raise TypeError("Exactly one argument (either uuid or username) must be provided.")


def get_online_wynncraft_players() -> set[str]:
    return _online_players


@tasks.loop(minutes=1)
async def update_players():
    global _online_players, _unknown_players
    now_online_players = set().union(*((await api.wynncraft.network.server_list()).values()))
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
