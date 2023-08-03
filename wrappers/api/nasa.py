import os
from dataclasses import dataclass

import utils.misc
from . import sessionManager, rateLimit

_nasa_rate_limit = rateLimit.RateLimit(1000, 60)
rateLimit.register_ratelimit(_nasa_rate_limit)

_nasa_api_session_id = sessionManager.register_session("https://api.nasa.gov")


@dataclass(frozen=True)
class APOD:
    copyright: str
    date: str
    explanation: str
    media_type: str
    title: str
    url: str


async def get_random_apod() -> APOD:
    """
    Get a random apod image from nasa.

    :return: The URL of the image.
    """
    session = sessionManager.get_session(_nasa_api_session_id)
    with _nasa_rate_limit:
        async with session.get("/planetary/apod",
                               params={"api_key": os.getenv('NASA_API_KEY'), "count": 1},
                               timeout=10
                               ) as resp:
            resp.raise_for_status()

            json = await resp.json()
            json = json[0]
            if "copyright" not in json:
                json["copyright"] = ""
            return utils.misc.dataclass_from_dict(APOD, json)
