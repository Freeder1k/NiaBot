from . import wynnAPI


def server_list():
    return wynnAPI.get_legacy("onlinePlayers")

def player_sum():
    return wynnAPI.get_legacy("onlinePlayersSum")['players_online']
