from dataclasses import dataclass
from datetime import date

from storage import manager


@dataclass(frozen=True)
class Strike:
    strike_id: int
    user_id: int
    server_id: int
    strike_date: str
    reason: str
    pardoned: bool


async def get_strikes(user_id: int, server_id: int) -> tuple[Strike]:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM strikes
                WHERE user_id = ?
                AND server_id = ?
            """, (user_id, server_id))

    data = await res.fetchall()

    return tuple(Strike(**{k: row[k] for k in row.keys()}) for row in data)


async def get_unpardoned_strikes_after(userid: int, server_id: int, day: date) -> tuple[Strike]:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM strikes
                WHERE user_id = ?
                AND server_id = ?
                AND pardoned = 0
                AND strike_date >= ?
            """, (userid, server_id, day))

    data = await res.fetchall()

    return tuple(Strike(**{k: row[k] for k in row.keys()}) for row in data)


async def get_strike_by_id(strike_id: int) -> Strike | None:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM strikes
                WHERE strike_id = ?
            """, (strike_id,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return Strike(**{k: data[0][k] for k in data[0].keys()})

async def add_strike(user_id: int, server_id: int, strike_date: date, reason: str):
    con = manager.get_connection()
    cur = manager.get_cursor()
    await cur.execute("""
            INSERT INTO strikes (user_id, server_id, strike_date, reason, pardoned)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, server_id, strike_date, reason))

    await con.commit()


async def pardon_strike(strike_id: int):
    con = manager.get_connection()
    cur = manager.get_cursor()
    await cur.execute("""
            UPDATE strikes
            SET pardoned = 1
            WHERE strike_id = ?
        """, (strike_id,))

    await con.commit()
