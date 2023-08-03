import aiosqlite

from . import guildMemberLogData

_con: aiosqlite.Connection = None


async def init_database():
    global _con
    if _con is not None:
        raise RuntimeError("init_database() was already called")
    _con = await aiosqlite.connect("./NiaBot.db")
    _con.row_factory = aiosqlite.Row

    cur = await _con.cursor()
    await cur.executescript(f"""
                    CREATE TABLE IF NOT EXISTS playtimes (
                        uuid TEXT NOT NULL,
                        day DATE NOT NULL,
                        playtime INTEGER NOT NULL,
                        PRIMARY KEY (uuid, day)
                    );
                    CREATE TABLE IF NOT EXISTS strikes (
                        strike_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        server_id INTEGER NOT NULL,
                        strike_date DATE NOT NULL,
                        reason TEXT NOT NULL,
                        pardoned INTEGER NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS minecraft_usernames (
                        uuid TEXT PRIMARY KEY NOT NULL,
                        name TEXT UNIQUE NOT NULL COLLATE NOCASE
                    );
                    CREATE TABLE IF NOT EXISTS guild_member_log(
                        log_id INTEGER PRIMARY KEY,
                        entry_type INTEGER CHECK(entry_type IN {tuple(t.value for t in guildMemberLogData.LogEntryType)}) NOT NULL,
                        content TEXT NOT NULL,
                        uuid TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                    );
    """)


def get_connection() -> aiosqlite.Connection:
    if _con is None:
        raise RuntimeError("call init_database() first")
    return _con


async def get_cursor() -> aiosqlite.Cursor:
    if _con is None:
        raise RuntimeError("call init_database() first")
    return await _con.cursor()


async def close():
    if _con is None:
        raise RuntimeError("call init_database() first")
    await _con.close()
