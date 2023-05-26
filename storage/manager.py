import sqlite3

_con = sqlite3.connect("./assets/NiaBot.db")
_con.row_factory = sqlite3.Row
_cur = _con.cursor()

# TODO async and threadsafe

def create_database():
    with _con:
        _cur.execute("""
            CREATE TABLE IF NOT EXISTS playtimes (
                player_uuid char(32),
                playtime_day date,
                playtime int,
                PRIMARY KEY (player_uuid, playtime_day)
            )
        """)


def get_connection():
    return _con


def get_cursor():
    return _cur


def close():
    _con.close()
