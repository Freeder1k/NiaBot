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
                        uuid TEXT NOT NULL COLLATE NOCASE,
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
                        uuid TEXT PRIMARY KEY NOT NULL COLLATE NOCASE,
                        name TEXT UNIQUE NOT NULL COLLATE NOCASE
                    );
                    CREATE TABLE IF NOT EXISTS guild_member_log(
                        log_id INTEGER PRIMARY KEY,
                        entry_type INTEGER CHECK(entry_type IN {tuple(t.value for t in guildMemberLogData.LogEntryType)}) NOT NULL,
                        content TEXT NOT NULL,
                        uuid TEXT NOT NULL COLLATE NOCASE,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS player_tracking (
                        record_time DATE NOT NULL,
                        uuid TEXT NOT NULL COLLATE NOCASE,
                        username TEXT NOT NULL COLLATE NOCASE,
                        rank TEXT,
                        support_rank TEXT,
                        first_join DATE,
                        last_join DATE,
                        playtime INTEGER,
                        guild_name TEXT,
                        guild_rank TEXT,
                        wars INTEGER,
                        total_levels INTEGER,
                        killed_mobs INTEGER,
                        chests_found INTEGER,
                        dungeons_total INTEGER,
                        dungeons_ds	INTEGER,
                        dungeons_ip INTEGER,
                        dungeons_ls INTEGER,
                        dungeons_uc INTEGER,
                        dungeons_ss INTEGER,
                        dungeons_ib INTEGER,
                        dungeons_gg INTEGER,
                        dungeons_ur INTEGER,
                        dungeons_cds INTEGER,
                        dungeons_cip INTEGER,
                        dungeons_cls INTEGER,
                        dungeons_css INTEGER,
                        dungeons_cuc INTEGER,
                        dungeons_cgg INTEGER,
                        dungeons_cur INTEGER,
                        dungeons_cib INTEGER,
                        dungeons_ff INTEGER,
                        dungeons_eo INTEGER,
                        dungeons_ts INTEGER,
                        raids_total INTEGER,
                        raids_notg INTEGER,
                        raids_nol INTEGER,
                        raids_tcc INTEGER,
                        raids_tna INTEGER,
                        completed_quests INTEGER,
                        pvp_kills INTEGER,
                        pvp_deaths INTEGER,
                        PRIMARY KEY (uuid, record_time)
                    );
    """)


def get_connection() -> aiosqlite.Connection:
    if _con is None:
        raise RuntimeError("call init_database() first")
    return _con


async def get_cursor() -> aiosqlite.Cursor:
    """
    Creates and returns a cursor object.
    """
    if _con is None:
        raise RuntimeError("call init_database() first")
    return await _con.cursor()


async def close():
    global _con
    if _con is None:
        raise RuntimeError("call init_database() first")
    await _con.close()
    _con = None
