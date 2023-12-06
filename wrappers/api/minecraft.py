from http import HTTPStatus

from handlers import rateLimit, reservableRateLimit
from niatypes.dataTypes import MinecraftPlayer
from . import sessionManager

_mojang_rate_limit = rateLimit.RateLimit(60, 1)
_usernames_rate_limit = reservableRateLimit.ReservableRateLimit(20, 1)

_mojang_api_session_id = sessionManager.register_session("https://api.mojang.com")


async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
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

    session = sessionManager.get_session(_mojang_api_session_id)
    with _mojang_rate_limit:
        async with session.get(request) as resp:
            if resp.status == HTTPStatus.NOT_FOUND:
                return None

            resp.raise_for_status()

            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            json = await resp.json()
            return MinecraftPlayer(json["id"], json["name"])


async def get_players_from_usernames(usernames: list[str]) -> list[MinecraftPlayer] | None:
    """
    Get the minecraft uuids of up to 10 users via the usernames.

    Any name that is under 25 characters and fits the regex ^(?=.*?(\w|^)(\w|$))((?![#&\\\|\/"])\w){1,25}$ will not trigger this error.

    :return: list of tuple of (case corrected username), (The uuid without "-") for each name that exists.
        or None if an error occurred.
    """
    if len(usernames) > 10:
        raise TypeError("usernames list can't contain more than 10 items!")

    session = sessionManager.get_session(_mojang_api_session_id)
    with _usernames_rate_limit:
        async with session.post(f"/profiles/minecraft", json=usernames) as resp:
            if resp.status == HTTPStatus.NOT_FOUND:
                return None

            resp.raise_for_status()

            if resp.status == HTTPStatus.NO_CONTENT:
                return None

            return [MinecraftPlayer(player["id"], player["name"]) for player in await resp.json()]


def uuid_to_avatar_url(uuid: str) -> str:
    """
    Get a crafatar url for the avatar of the uuid.
    """
    return f"https://crafatar.com/avatars/{uuid}?overlay=True"
