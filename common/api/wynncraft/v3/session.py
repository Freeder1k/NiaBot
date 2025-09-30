import asyncio
import os

import aiohttp

from common.api import sessionManager
from common.api.wynncraft.v3.wynnRateLimit import WynnRateLimit
from common.types.jsonable import JsonType

from dotenv import load_dotenv
load_dotenv()

_shared_rate_limit = WynnRateLimit()
_v3_session_id = sessionManager.register_session("https://api.wynncraft.com")



async def get(url: str, rate_limit=None, api_key=None, tries=0, **params: str) -> JsonType:
    """
    Send a GET request to the wynncraft API V3. This has a ratelimit of 180 requests per minute.
    :param url: The url of the request. Must start with '/'.
    :param rate_limit: If set, the specified rate limit will be used instead of the shared one.
    :param api_key: Optional API key for accessing private stats.
    :param tries: The number of times this request has been attempted.
    :param params: Additional request parameters.
    :return: the response in json format.
    """
    if rate_limit is None:
        rate_limit = _shared_rate_limit

    if api_key is None:
        api_key = os.getenv('WYNN_API_KEY')

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with rate_limit:
            session = sessionManager.get_session(_v3_session_id)
            async with session.get(f"/v3{url}", params=params, raise_for_status=True, headers=headers) as resp:
                _rl_reset = resp.headers.get("ratelimit-reset")
                _rl_reset = int(_rl_reset) if _rl_reset else 0
                if _rl_reset > 0:
                    rate_limit.set_time_until_reset(_rl_reset)

                remaining = resp.headers.get("ratelimit-remaining")
                remaining = int(remaining) if remaining else 0
                rate_limit.set_remaining(remaining)

                return await resp.json()
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 500:
            if tries >= 1:
                raise ex
            await asyncio.sleep(0.1)
            return await get(url, rate_limit=rate_limit, api_key=api_key, tries=tries+1, **params)
        else:
            raise ex


def calculate_remaining_requests():
    return _shared_rate_limit.calculate_remaining_calls()


def ratelimit_reset_time():
    return _shared_rate_limit.get_time_until_reset()
