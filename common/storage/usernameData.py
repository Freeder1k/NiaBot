from common.types.dataTypes import MinecraftPlayer
from . import manager


async def get_players(*, uuids: list[str] = None, usernames: list[str] = None) -> list[MinecraftPlayer]:
    """
    Get a list of players by uuids and names.

    :return: A list containing all players that were found.
    """
    if uuids is None or len(uuids) == 0:
        uuids = [""]
    if usernames is None or len(usernames) == 0:
        usernames = [""]

    uuids = [uuid.replace("-", "").lower() for uuid in uuids]

    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE uuid IN ({', '.join("?" for _ in uuids)})
                OR name in ({', '.join("?" for _ in usernames)})
                """, uuids + usernames)

    data = await res.fetchall()

    return [MinecraftPlayer(row["uuid"], row["name"]) for row in data]


async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    """
    Get a player by either their uuid or username. Exactly one of the arguments must be provided.

    :return: The player or None if not found.
    """
    if (uuid is None) and (username is not None):
        selector = "name"
        match = username
    elif (uuid is not None) and (username is None):
        selector = "uuid"
        match = uuid.replace("-", "").lower()
    else:
        raise TypeError("Exactly one argument (either uuid or username) must be provided.")

    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE {selector} = ?
                """, (match,))

    data = tuple(await res.fetchall())
    if len(data) == 0:
        return None

    return MinecraftPlayer(data[0]["uuid"], data[0]["name"])


async def find_players(s: str) -> list[MinecraftPlayer]:
    """
    Find all players that have a name starting with the specified string.

    :return: A list of all players that were found.
    """
    cur = await manager.get_cursor()
    res = await cur.execute(f"""
                SELECT * FROM minecraft_usernames
                WHERE name LIKE ?
                """, (f"{s.lower()}%",))

    data = await res.fetchall()

    return [MinecraftPlayer(row["uuid"], row["name"]) for row in data]


async def update(uuid: str, username: str) -> MinecraftPlayer | None:
    """
    Update a player in the database. If any entries exist with the same uuid or (case-insensitive) username these get replaced.

    :return: The previous player associated with the uuid or None if none was associated.
    """
    uuid = uuid.replace("-", "").lower()

    con = manager.get_connection()
    cur = await manager.get_cursor()

    prev_p = await get_player(uuid=uuid)
    if prev_p is None or prev_p.name != username:
        await cur.execute("""
                REPLACE INTO minecraft_usernames VALUES (?, ?)
                """, (uuid, username))

        await con.commit()

    return prev_p
