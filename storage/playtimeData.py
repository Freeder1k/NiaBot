import asyncio
from dataclasses import dataclass
from datetime import date, time, timezone, datetime

from discord.ext import tasks

import api.wynncraft.guild
import api.wynncraft.player
from api import minecraft
from storage import manager


@dataclass(frozen=True)
class Playtime:
    uuid: str
    day: str
    playtime: int


async def get_playtime(uuid: str, day: date) -> Playtime | None:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM playtimes
                WHERE uuid = ?
                AND day = ?
            """, (uuid, day))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return Playtime(**{k: data[0][k] for k in data[0].keys()})


async def get_all_playtimes(uuid: str) -> tuple[Playtime]:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM playtimes
                WHERE uuid = ?
            """, (uuid,))

    return tuple(Playtime(data["player_uuid"], data["playtime_day"], data["playtime"]) for data in await res.fetchall())


async def set_playtime(uuid: str, day: date, playtime: int):
    uuid = uuid.replace("-", "")

    con = manager.get_connection()
    cur = manager.get_cursor()
    await cur.execute("""
            REPLACE INTO playtimes VALUES (?, ?, ?)
        """, (uuid, day, playtime))

    await con.commit()


async def get_first_date_after(date_before: date) -> date | None:
    cur = manager.get_cursor()
    res = await cur.execute("""
                    SELECT min(day) FROM playtimes
                    WHERE day >= ?
                """, (date_before,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None
    if 'min(day)' not in data[0].keys():
        return None
    return data[0]['min(day)']


async def get_first_date_after_from_uuid(date_before: date, uuid: str) -> date | None:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                    SELECT min(day) FROM playtimes
                    WHERE uuid = ?
                    AND day >= ?
                """, (uuid, date_before))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None
    if 'min(day)' not in data[0].keys():
        return None
    return data[0]['min(day)']


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc))
async def update_playtimes():
    nia = await api.wynncraft.guild.stats("Nerfuria")
    today = datetime.now(timezone.utc).date()

    usernames = await asyncio.gather(*tuple(minecraft.uuid_to_username(m.uuid) for m in nia.members))
    res: list[api.wynncraft.player.Stats] = await asyncio.gather(
        *(api.wynncraft.player.stats(name) for name in usernames))

    await asyncio.gather(*(set_playtime(stats.uuid, today, stats.meta.playtime) for stats in res))
