from http import HTTPStatus

import aiohttp
from aiohttp import ClientSession

from api import rateLimit, reservableRateLimit
from data_types import Player

# TODO create accessing methods for reservations
_mojang_rate_limit = rateLimit.RateLimit(60, 1)
rateLimit.register_ratelimit(_mojang_rate_limit)
_usernames_rate_limit = reservableRateLimit.ReservableRateLimit(20, 0)
rateLimit.register_ratelimit(_usernames_rate_limit)

_mojang_api_session: ClientSession = None


def format_uuid(uuid: str) -> str:
    """
    Add the "-" to a uuid.
    """
    return "-".join((uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32]))


async def get_player(*, uuid: str = None, username: str = None) -> Player | None:
    """
    Get a player via either their uuid or their username. Exactly one argument must be provided.
    May raise a RatelimitException or ClientResponseError.

    :return: A player object if the player exists otherwise None.
    """
    if (uuid is None) and (username is not None):
        request = f"/users/profiles/minecraft/{username}"
    elif (uuid is not None) and (username is None):
        request = f"/user/profile/{uuid}"
    else:
        raise TypeError("Exactly one argument (either uuid or username) must be provided.")

    with _mojang_rate_limit:
        async with _mojang_api_session.get(request) as resp:
            if resp.status == HTTPStatus.NOT_FOUND:
                return None

            resp.raise_for_status()

            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            json = await resp.json()
            return Player(json["id"], json["name"])


async def get_players_from_usernames(usernames: list[str], reservation_id: int = -1) -> list[Player] | None:
    """
    Get the minecraft uuids of up to 10 users via the usernames.

    Any name that is under 25 characters and fits the regex ^(?=.*?(\w|^)(\w|$))((?![#&\\\|\/"])\w){1,25}$ will not trigger this error.

    :return: list of tuple of (case corrected username), (The uuid without "-") for each name that exists.
        or None if an error occurred.
    """
    if len(usernames) > 10:
        raise TypeError("usernames list can't contain more than 10 items!")

    if reservation_id == -1:
        rlimit = _usernames_rate_limit
    else:
        rlimit = _usernames_rate_limit.get_reservation(reservation_id)

    with rlimit:
        async with _mojang_api_session.post(f"/profiles/minecraft", json=usernames) as resp:
            if resp.status == HTTPStatus.NOT_FOUND:
                return None

            resp.raise_for_status()

            if resp.status == HTTPStatus.NO_CONTENT:
                return None

            return [Player(player["id"], player["name"]) for player in await resp.json()]


def uuid_to_avatar_url(uuid: str) -> str:
    """
    Get a crafatar url for the avatar of the uuid.
    """
    return f"https://crafatar.com/avatars/{uuid}?overlay=True"


async def init_session():
    global _mojang_api_session
    _mojang_api_session = aiohttp.ClientSession("https://api.mojang.com")


async def close():
    await _mojang_api_session.close()
