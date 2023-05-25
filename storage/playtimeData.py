from dataclasses import dataclass
from datetime import date

from storage import manager


@dataclass(frozen=True)
class Playtime:
    uuid: str
    day: date
    playtime: int


def get_playtime(uuid: str, day: date) -> Playtime | None:
    con = manager.get_connection()
    cur = manager.get_cursor()
    with con:
        res = cur.execute("""
            SELECT * FROM playtimes
            WHERE player_uuid = ?
            AND playtime_day = ?
        """, (uuid, day))

        data = res.fetchone()
        if data is None:
            return None

        return Playtime(data["player_uuid"], data["playtime_day"], data["playtime"])


def get_all_playtimes(uuid: str) -> tuple[Playtime]:
    con = manager.get_connection()
    cur = manager.get_cursor()
    with con:
        res = cur.execute("""
            SELECT * FROM playtimes
            WHERE player_uuid = ?
        """, (uuid,))

        return tuple(Playtime(data["player_uuid"], data["playtime_day"], data["playtime"]) for data in res.fetchall())


def set_playtime(uuid: str, day: date, playtime: int):
    con = manager.get_connection()
    cur = manager.get_cursor()
    with con:
        cur.execute("""
            REPLACE INTO playtimes VALUES (?, ?, ?)
        """, (uuid, day, playtime))
