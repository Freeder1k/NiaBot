import time

from handlers import reservableRateLimit
from handlers.rateLimit import RateLimit
from niatypes.jsonable import JsonType
from wrappers.api import sessionManager

_rate_limit = reservableRateLimit.ReservableRateLimit(180, 1)
_v3_session_id = sessionManager.register_session("https://api.wynncraft.com")
_rl_reset = 0
_last_req_time = 0


async def get(url: str, **params: str) -> JsonType:
    """
    Send a GET request to the wynncraft API V3. This has a ratelimit of 300 requests per minute.
    :param url: The url of the request. Must start with '/'.
    :param params: Additional request parameters.
    :return: the response in json format.
    """
    with _rate_limit:
        session = sessionManager.get_session(_v3_session_id)
        async with session.get(f"/v3{url}", params=params) as resp:
            global _rl_reset, _last_req_time
            _rl_reset = int(resp.headers.get("ratelimit-reset"))
            _last_req_time = time.time()
            remaining = int(resp.headers.get("x-ratelimit-remaining-minute"))
            if remaining == 0:
                _rate_limit._set_full()

            resp.raise_for_status()
            return await resp.json()


def reserve(amount: int) -> RateLimit:
    """
    Reserve amount requests.
    :param amount: the amount of requests to reserve
    :returns: A ratelimit for the reservation.
    """
    return _rate_limit.reserve(amount)


def calculate_remaining_requests():
    return _rate_limit.calculate_remaining_calls()


def ratelimit_reset_time():
    return max(_rl_reset + _last_req_time - time.time(), 0)
