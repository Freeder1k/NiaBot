from dataclasses import dataclass
from datetime import date

from storage import manager


@dataclass(frozen=True)
class Strike:
    strike_id: int
    user_id: int
    strike_date: date
    reason: str
    pardoned: bool


async def get_strikes(userid: int) -> tuple[Strike]:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM strikes
                WHERE user_id = ?
            """, (userid,))

    data = await res.fetchall()

    return tuple(Strike(**{k: res[k] for k in res.keys()}) for res in data)


async def get_strikes_after(userid: int, day: date) -> tuple[Strike]:
    cur = manager.get_cursor()
    res = await cur.execute("""
                SELECT * FROM strikes
                WHERE user_id = ?
                AND strike_date >= ?
            """, (userid, day))

    data = await res.fetchall()

    return tuple(Strike(**{k: res[k] for k in res.keys()}) for res in data)


async def add_strike(user_id: int, strike_date: date, reason: str):
    con = manager.get_connection()
    cur = manager.get_cursor()
    await cur.execute("""
            INSERT INTO strikes (user_id, strike_date, reason, pardoned)
            VALUES (?, ?, ?, 0)
        """, (user_id, strike_date, reason))

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
