import aiosqlite

_con: aiosqlite.Connection = None
_cur: aiosqlite.Cursor = None


async def init_database():
    global _cur, _con
    _con = await aiosqlite.connect("./NiaBot.db")
    _con.row_factory = aiosqlite.Row
    _cur = await _con.cursor()

    await _cur.execute("""
                CREATE TABLE IF NOT EXISTS playtimes (
                    uuid TEXT,
                    day DATE,
                    playtime INTEGER,
                    PRIMARY KEY (uuid, day)
                )
            """)
    await _cur.execute("""
                    CREATE TABLE IF NOT EXISTS strikes (
                        strike_id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        strike_date DATE,
                        reason TEXT
                    )
                """)


def get_connection() -> aiosqlite.Connection:
    return _con


def get_cursor() -> aiosqlite.Cursor:
    return _cur


async def close():
    await _con.close()
