import requests
from api import rateLimit

mojang_rate_limit = rateLimit.RateLimit(600, 10)
rateLimit.add_ratelimit(mojang_rate_limit)

sessionserver_rate_limit = rateLimit.RateLimit(200, 1)
rateLimit.add_ratelimit(sessionserver_rate_limit)


def format_uuid(uuid: str) -> str:
    """
    Add the "-" to a uuid.
    """
    return "-".join((uuid[:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:32]))


def username_to_uuid(username: str) -> str | None:
    """
    Get the minecraft username of a user via the uuid.

    :return: None, if the name doesn't exist. The uuid without "-" otherwise.
    """
    with mojang_rate_limit:
        request = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}')
        if request.status_code == 204:
            return None
        return request.json()["id"]


def uuid_to_username(uuid: str) -> str | None:
    """
    Get the minecraft uuid of a user via the username.

    :return: None, if the uuid doesn't exist. The username otherwise.
    """
    with sessionserver_rate_limit:
        request = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}')
        if request.status_code == 204:
            return None
        return request.json()["name"]
