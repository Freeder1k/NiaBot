from dataclasses import dataclass
from datetime import date

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
