from . import wynnAPI


async def server_list() -> dict[str, list[str]]:
    """
    Returns which servers are online and which players are on them.
    """
    return await wynnAPI.get_legacy("onlinePlayers")


async def online_players() -> frozenset[str]:
    """
    Returns a set of the names of all currently online players.
    """
    return frozenset().union(*((await server_list()).values()))


async def player_count() -> int:
    """
    Returns the amount of players online on the Wynncraft network.
    """
    return (await wynnAPI.get_legacy("onlinePlayersSum"))['players_online']
