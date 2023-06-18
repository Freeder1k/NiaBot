from . import wynnAPI


async def server_list() -> dict[str, list[str]]:
    return await wynnAPI.get_legacy("onlinePlayers")


async def player_sum() -> int:
    return (await wynnAPI.get_legacy("onlinePlayersSum"))['players_online']
