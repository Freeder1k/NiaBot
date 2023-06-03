import asyncio
from dataclasses import dataclass
from datetime import date, time, timezone, datetime

from discord.ext import tasks

import api.wynncraft.guild
import api.wynncraft.player
from storage import manager


@dataclass(frozen=True)
class Playtime:
    uuid: str
    day: date
    playtime: int


async def get_playtime(uuid: str, day: date) -> Playtime | None:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM playtimes
                WHERE player_uuid = ?
                AND playtime_day = ?
            """, (uuid, day))

    data = await res.fetchone()
    if data is None:
        return None

    return Playtime(data["player_uuid"], data["playtime_day"], data["playtime"])


async def get_all_playtimes(uuid: str) -> tuple[Playtime]:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM playtimes
                WHERE player_uuid = ?
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
                    SELECT min(playtime_day) FROM playtimes
                    WHERE playtime_day >= ?
                """, (date_before,))

    data = await res.fetchone()
    if data is None:
        return None
    if 'min(playtime_day)' not in data.keys():
        return None
    return data['min(playtime_day)']


async def get_first_date_after_from_uuid(date_before: date, uuid: str) -> date | None:
    uuid = uuid.replace("-", "")

    cur = manager.get_cursor()
    res = await cur.execute("""
                    SELECT min(playtime_day) FROM playtimes
                    WHERE player_uuid = ?
                    AND playtime_day >= ?
                """, (uuid, date_before))

    data = await res.fetchone()
    if data is None:
        return None
    if 'min(playtime_day)' not in data.keys():
        return None
    return data['min(playtime_day)']


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc))
async def update_playtimes():
    nia = await api.wynncraft.guild.stats("Nerfuria")
    today = datetime.now(timezone.utc).date()

    res: list[api.wynncraft.player.Stats] = await asyncio.gather(
        *(api.wynncraft.player.stats(member.uuid) for member in nia.members))

    await asyncio.gather(*(set_playtime(stats.uuid, today, stats.meta.playtime) for stats in res))
