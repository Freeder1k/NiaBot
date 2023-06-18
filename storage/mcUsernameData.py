import asyncio
from queue import Queue

from discord.ext import tasks

import api.minecraft
import api.wynncraft.network
import api.wynncraft.wynnAPI
import utils.logging
from storage import manager

online_players = set()
unknown_players = Queue()


async def get_username(uuid: str) -> str | None:
    uuid = uuid.replace("-", "").lower()

    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT name FROM minecraft_usernames
                WHERE uuid = ?
                """, (uuid,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return data[0]["name"]


async def get_usernames(*uuids: str) -> dict[str, str]:
    uuids = [uuid.replace("-", "").lower() for uuid in uuids]

    cur = manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE uuid IN ({', '.join("?" for _ in uuids)})
                """, uuids)

    data = await res.fetchall()
    return {row["uuid"]: row["name"] for row in data}


async def get_uuid(username: str) -> str | None:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT uuid FROM minecraft_usernames
                WHERE name = ?
                """, (username,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return data[0]["uuid"]


async def get_uuids(*usernames: str) -> dict[str, str]:
    cur = manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE name IN ({', '.join("?" for _ in usernames)})
                """, usernames)

    data = (await res.fetchall())
    return {row["name"]: row["uuid"] for row in data}


async def get_player(*, uuid: str = None, username: str = None) -> tuple[str, str] | None:
    if (uuid is None) and (username is not None):
        selector = "name"
        match = username
    elif (uuid is not None) and (username is None):
        selector = "uuid"
        match = uuid
    else:
        raise TypeError("Exactly one argument (either uuid or username) must be provided.")

    cur = manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE {selector} = ?
                """, (match,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return data[0]["uuid"], data[0]["name"]


async def update(uuid: str, username: str) -> str | None:
    uuid = uuid.replace("-", "").lower()

    con = manager.get_connection()
    cur = manager.get_cursor()

    prev_username = await get_username(uuid)
    if prev_username is None or prev_username != username:
        await cur.execute("""
                REPLACE INTO minecraft_usernames VALUES (?, ?)
                """, (uuid, username))

    await con.commit()

    return prev_username


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@tasks.loop(minutes=1)
async def update_players():
    global online_players, unknown_players
    now_online_players = set().union(*((await api.wynncraft.network.server_list()).values()))
    new_joins = now_online_players - online_players
    online_players = now_online_players

    known_players = await get_uuids(*new_joins)
    unknown_joined_players = [name for name in new_joins if name not in known_players]
    for i in range(0, len(unknown_joined_players), 10):
        unknown_players.put(unknown_joined_players[i:i + 10])
    if not unknown_players.empty():
        utils.logging.dlog(
            f"Updating {sum((len(unknown_players.queue[i]) for i in range(min(unknown_players.qsize(), 20))))}"
            f" minecraft usernames.")

    for i in range(0, min(unknown_players.qsize(), 20)):
        curr_unkn_p = unknown_players.get()

        res = await api.minecraft.usernames_to_uuids(curr_unkn_p)
        await asyncio.gather(*(update(uuid, name) for name, uuid in res))

        for name in curr_unkn_p:
            if not any(name == t_name for t_name, _ in res):
                utils.logging.dlog(f"{name} not a minecraft name but online on wynncraft!")
