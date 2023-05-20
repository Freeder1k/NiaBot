from wynncraft import wynnAPI


def server_list():
    wynnAPI.get_legacy("onlinePlayers")

def player_sum():
    return wynnAPI.get_legacy("onlinePlayersSum")['players_online']
