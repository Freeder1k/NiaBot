import requests
from . import rateLimit

legacy_rate_limit = rateLimit.RateLimit(1200, 20)
rateLimit.add_ratelimit(legacy_rate_limit)

def get_legacy(action: str, command: str = ""):
    with legacy_rate_limit:
        json = requests.get(f'https://api-legacy.wynncraft.com/public_api.php?action={action}&command={command}').json()
        json.pop("request")
        return json


def get_v2(url: str):
    r = requests.get(f'https://api.wynncraft.com/v2{url}')
    return r.json()