from common.api import sessionManager
from common.api.wynncraft.v3.wynnRateLimit import WynnRateLimit
from common.types.jsonable import JsonType

_rate_limit = WynnRateLimit()
_v3_session_id = sessionManager.register_session("https://api.wynncraft.com")


async def get(url: str, **params: str) -> JsonType:
    """
    Send a GET request to the wynncraft API V3. This has a ratelimit of 180 requests per minute.
    :param url: The url of the request. Must start with '/'.
    :param params: Additional request parameters.
    :return: the response in json format.
    """
    with _rate_limit:
        session = sessionManager.get_session(_v3_session_id)
        async with session.get(f"/v3{url}", params=params, raise_for_status=True) as resp:
            _rl_reset = resp.headers.get("ratelimit-reset")
            _rl_reset = int(_rl_reset) if _rl_reset else 0
            if _rl_reset > 0:
                _rate_limit.set_time_until_reset(_rl_reset)

            remaining = resp.headers.get("x-ratelimit-remaining-minute")
            remaining = int(remaining) if remaining else 0
            _rate_limit.set_remaining(remaining)

            return await resp.json()


def calculate_remaining_requests():
    return _rate_limit.calculate_remaining_calls()


def ratelimit_reset_time():
    return _rate_limit.get_time_until_next_free()
