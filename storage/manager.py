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
                    uuid TEXT NOT NULL,
                    day DATE NOT NULL,
                    playtime INTEGER NOT NULL,
                    PRIMARY KEY (uuid, day)
                )
            """)
    await _cur.execute("""
                    CREATE TABLE IF NOT EXISTS strikes (
                        strike_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        server_id INTEGER NOT NULL,
                        strike_date DATE NOT NULL,
                        reason TEXT NOT NULL,
                        pardoned INTEGER NOT NULL
                    )
                """)


def get_connection() -> aiosqlite.Connection:
    return _con


def get_cursor() -> aiosqlite.Cursor:
    return _cur


async def close():
    await _con.close()
