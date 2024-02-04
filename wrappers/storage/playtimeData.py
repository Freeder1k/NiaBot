import asyncio
from dataclasses import dataclass
from datetime import date, time, timezone, datetime

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import handlers.rateLimit
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.types
import wrappers.botConfig
from . import manager


@dataclass(frozen=True)
class Playtime:
    uuid: str
    day: str
    playtime: int


async def get_playtime(uuid: str, day: date) -> Playtime | None:
    uuid = uuid.replace("-", "").lower()

    cur = await manager.get_cursor()
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
    uuid = uuid.replace("-", "").lower()

    cur = await manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM playtimes
                WHERE uuid = ?
                ORDER BY day
            """, (uuid,))

    return tuple(Playtime(data["uuid"], data["day"], data["playtime"]) for data in await res.fetchall())


async def set_playtime(uuid: str, day: date, playtime: int):
    uuid = uuid.replace("-", "").lower()

    con = manager.get_connection()
    cur = await manager.get_cursor()
    await cur.execute("""
            REPLACE INTO playtimes VALUES (?, ?, ?)
        """, (uuid, day, playtime))

    await con.commit()


async def get_first_date_after(date_before: date) -> date | None:
    cur = await manager.get_cursor()
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
    uuid = uuid.replace("-", "").lower()

    cur = await manager.get_cursor()
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


async def _update_playtime(uuid: str):
    try:
        stats = await wrappers.api.wynncraft.v3.player.stats(uuid)
        await set_playtime(stats.uuid, datetime.now(timezone.utc).date(), int(stats.playtime * 60))
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
        handlers.logging.error(f'Failed to fetch stats for guild member with uuid {uuid}')


@tasks.loop(time=time(hour=0, minute=0, tzinfo=timezone.utc), reconnect=True)
async def update_playtimes():
    try:
        guild = await wrappers.api.wynncraft.v3.guild.stats(name=wrappers.botConfig.GUILD_NAME)

        await asyncio.gather(*(_update_playtime(uuid) for uuid in guild.members.all.keys()))
    except Exception as ex:
        await handlers.logging.error(exc_info=ex)
        raise ex


update_playtimes.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
