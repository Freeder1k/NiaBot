import requests
from wynncraft import rateLimit

legacy_rate_limit = rateLimit.RateLimit(1200, 20)
rateLimit.add_ratelimit(legacy_rate_limit)

def get_legacy(action: str):
    with legacy_rate_limit:
        r = requests.get(f'https://api-legacy.wynncraft.com/public_api.php?action={action}')
        return r.json()


def get_v2(url: str):
    r = requests.get(f'https://api.wynncraft.com/v2{url}')
    return r.json()