import requests


def get_legacy(action: str):
    r = requests.get(f'https://api-legacy.wynncraft.com/public_api.php?action={action}')
    return r.json()


def get_v2(url: str):
    r = requests.get(f'https://api.wynncraft.com/v2{url}')
    return r.json()