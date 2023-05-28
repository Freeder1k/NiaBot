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
                    player_uuid char(32),
                    playtime_day date,
                    playtime int,
                    PRIMARY KEY (player_uuid, playtime_day)
                )
            """)


def get_connection() -> aiosqlite.Connection:
    return _con


def get_cursor() -> aiosqlite.Cursor:
    return _cur


async def close():
    await _con.close()
