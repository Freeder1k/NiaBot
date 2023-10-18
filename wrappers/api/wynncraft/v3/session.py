from handlers import reservableRateLimit
from handlers.rateLimit import RateLimit
from wrappers.api import sessionManager

_rate_limit = reservableRateLimit.ReservableRateLimit(300, 1)
_v3_session_id = sessionManager.register_session("https://api.wynncraft.com")


async def get(url: str, **params: str) -> dict:
    """
    Send a GET request to the wynncraft API V3. This has a ratelimit of 300 requests per minute.
    :param url: The url of the request. Must start with '/'.
    :param params: Additional request parameters.
    :return: the response in json format.
    """
    session = sessionManager.get_session(_v3_session_id)
    async with session.get(f"/v3{url}", params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


def reserve(amount: int) -> RateLimit:
    """
    Reserve amount requests.
    :param amount: the amount of requests to reserve
    :returns: A ratelimit for the reservation.
    """
    return _rate_limit.reserve(amount)
