from . import wynnAPI


async def server_list() -> dict[str, list[str]]:
    """
    Returns which servers are online and which players are on them.
    """
    return await wynnAPI.get_legacy("onlinePlayers")


async def player_sum() -> int:
    """
    Returns the player sum on the Wynncraft network.
    """
    return (await wynnAPI.get_legacy("onlinePlayersSum"))['players_online']
