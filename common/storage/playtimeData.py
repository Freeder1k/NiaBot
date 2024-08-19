from dataclasses import dataclass
from datetime import date

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
