from . import wynnAPI


async def server_list():
    return await wynnAPI.get_legacy("onlinePlayers")


async def player_sum():
    return (await wynnAPI.get_legacy("onlinePlayersSum"))['players_online']
