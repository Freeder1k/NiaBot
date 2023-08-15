from niatypes.dataTypes import WynncraftGuild
from . import manager


async def get_guild(*, tag: str = None, name: str = None) -> WynncraftGuild | None:
    """
    Get a guild by either the tag or name. Exactly one of the arguments must be provided.

    :return: The player or None if not found.
    """
    if (tag is None) and (name is not None):
        selector = "name"
        match = name
    elif (tag is not None) and (name is None):
        selector = "tag"
        match = tag
    else:
        raise TypeError("Exactly one argument (either tah or name) must be provided.")

    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM guilds
                WHERE {selector} = ?
                """, (match,))
    row = await res.fetchone()
    if row is None:
        return None

    return WynncraftGuild(row["tag"], row["name"])


async def find_guilds(s: str) -> tuple[WynncraftGuild]:
    """
    Returns any guilds whose tag or name matches the provided string (case-insensitive).

    :return: A tuple of guilds.
    """
    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM guilds
                WHERE tag COLLATE NOCASE = ?
                OR name = ?
                """, (s, s))
    data = await res.fetchall()

    return tuple(WynncraftGuild(row["tag"], row["name"]) for row in data)


async def guild_list() -> tuple[str]:
    """
    Returns a list of all stored guilds names.
    """
    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT name FROM guilds
                """)
    data = await res.fetchall()
    return tuple(str(row["name"]) for row in data)


async def put(tag: str, name: str):
    """
    Puts a guild into the database. If any entries exist with the same tag or (case-insensitive) name these get replaced.
    """
    con = manager.get_connection()
    cur = await manager.get_cursor()
    await cur.execute("""
                REPLACE INTO guilds VALUES (?, ?)
                """, (tag, name))
    await con.commit()


async def remove(*, tag: str = None, name: str = None):
    """
    Remove the specified guild from the database. . Exactly one of the arguments must be provided.
    """
    if (tag is None) and (name is not None):
        selector = "name"
        match = name
    elif (tag is not None) and (name is None):
        selector = "tag"
        match = tag
    else:
        raise TypeError("Exactly one argument (either tag or name) must be provided.")

    con = manager.get_connection()
    cur = await manager.get_cursor()

    await cur.execute(f"""
                DELETE FROM guilds
                WHERE {selector} = ?
                """, (match,))
    await con.commit()


async def remove_many(*, tags: list[str] = None, names: list[str] = None):
    """
    Removes the provided list of tags and guild names from the database.
    """
    if tags is None or len(tags) == 0:
        tags = [""]
    if names is None or len(names) == 0:
        names = [""]

    con = manager.get_connection()
    cur = await manager.get_cursor()
    await cur.execute(f"""
                DELETE FROM guilds
                WHERE tag IN ({', '.join("?" for _ in tags)})
                OR name in ({', '.join("?" for _ in names)})
                """, tags + names)
    await con.commit()
