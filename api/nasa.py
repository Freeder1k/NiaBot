import os
from dataclasses import dataclass

import aiohttp
from aiohttp import ClientSession

import utils.misc
from api import rateLimit

_nasa_rate_limit = rateLimit.RateLimit(1000, 60)
rateLimit.add_ratelimit(_nasa_rate_limit)

_nasa_api_session: ClientSession = None


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
    with _nasa_rate_limit:
        async with _nasa_api_session.get("/planetary/apod",
                                         params={"api_key": os.getenv('NASA_API_KEY'), "count": 1}) as resp:
            json = await resp.json()
            json = json[0]
            if "copyright" not in json:
                json["copyright"] = ""
            return utils.misc.dataclass_from_dict(APOD, json)


async def init_session():
    global _nasa_api_session
    _nasa_api_session = aiohttp.ClientSession("https://api.nasa.gov")


async def close():
    await _nasa_api_session.close()
