from http import HTTPStatus

from common.types.dataTypes import MinecraftPlayer
from . import sessionManager, rateLimit

_mojang_rate_limit = rateLimit.RateLimit(200, 1)
_mc_services_rate_limit = rateLimit.RateLimit(10, 1)

_mojang_api_session_id = sessionManager.register_session("https://api.mojang.com")
_mc_services_api_session_id = sessionManager.register_session("https://api.minecraftservices.com")


async def get_player(*, uuid: str = None, username: str = None) -> MinecraftPlayer | None:
    """
    Get a player via either their uuid or their username. Exactly one argument must be provided.
    May raise a RatelimitException or ClientResponseError.

    :return: A player object if the player exists otherwise None.
    """
    if (uuid is None) and (username is not None):
        request = f"/users/profiles/minecraft/{username}"
    elif (uuid is not None) and (username is None):
        # alternative: https://sessionserver.mojang.com/session/minecraft/profile/{uuid}
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

def calculate_remaining_calls() -> int:
    """
    Calculate the remaining calls to the mojang api.
    """
    return _mojang_rate_limit.calculate_remaining_calls()


async def get_players(usernames: list[str]) -> dict[str, MinecraftPlayer]:
    """
    Get the minecraft uuids of up to 10 users via the usernames.

    :return: Dictionary of usernames mapped to a MinecraftPlayer object for all players that exist.
    """
    if len(usernames) > 10:
        raise TypeError("usernames list can't contain more than 10 items!")

    json = '[' + ','.join([f'"{name}"' for name in usernames]) + ']'

    session = sessionManager.get_session(_mc_services_api_session_id)
    with _mc_services_rate_limit:
        async with session.post(f"/minecraft/profile/lookup/bulk/byname", json=json) as resp:
            resp.raise_for_status()

            return {player["name"]: MinecraftPlayer(player["id"], player["name"]) for player in await resp.json()}


def uuid_to_avatar_url(uuid: str) -> str:
    """
    Get a crafatar url for the avatar of the uuid.
    """
    return f"https://crafatar.com/avatars/{uuid}?overlay=True"
