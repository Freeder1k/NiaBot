import time

import aiohttp.client_exceptions
from async_lru import alru_cache

import common.utils.misc
from common.api.wynncraft.v3 import session
from common.api.wynncraft.v3.wynnRateLimit import WynnRateLimit
from common.types.enums import PlayerIdentifier
from common.types.wynncraft import PlayerStats, CharacterShort, AbilityNode


_player_rate_limit = WynnRateLimit()

class UnknownPlayerException(Exception):
    pass


class HiddenProfileException(Exception):
    pass


@alru_cache(maxsize=None, ttl=30)
async def stats(uuid: str, full_result: bool = False) -> PlayerStats:
    """
    Request public statistical information about a player.
    :param uuid: The uuid of the player to retrieve the stats of.
    :param full_result: If True, the character list is included in the result.
    :returns: A Stats object.
    :raises ValueError: if the uuid is not in a valid format.
    :raises UnknownPlayerException: if the player wasn't found.
    """
    uuid = common.utils.misc.format_uuid(uuid, dashed=True)

    try:
        data = await session.get(f"/player/{uuid}", fullResult="", rate_limit=_player_rate_limit)
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 404:
            raise UnknownPlayerException(f'Player {uuid} not found.')
        else:
            raise ex

    return PlayerStats.from_json(data)


@alru_cache(maxsize=None, ttl=30)
async def characters(uuid: str) -> dict[str, CharacterShort]:
    """
    Request a list of short info on a players characters.
    :param uuid: The uuid of the player to retrieve the characters of.
    :returns: A dictionary of character_uuids mapped to a CharacterShort object.
    :raises ValueError: if the uuid is not in a valid format.
    :raises UnknownPlayerException: if the player wasn't found.
    """
    uuid = common.utils.misc.format_uuid(uuid, dashed=True)

    try:
        data = await session.get(f"/player/{uuid}/characters", rate_limit=_player_rate_limit)
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 404:
            raise UnknownPlayerException(f'Player {uuid} not found.')
        else:
            raise ex

    return {uuid: CharacterShort.from_json(data) for uuid, data in data.items()}


@alru_cache(maxsize=None, ttl=600)
async def abilities(player_uuid: str, character_uuid: str) -> list[AbilityNode]:
    """
    Request the ability map of the specified character.
    :param player_uuid: The uuid of the player to retrieve the ability map of.
    :param character_uuid: The specific character uuid.
    :returns: An AbilityMap object.
    :raises ValueError: if the player uuid is not in a valid format.
    :raises UnknownPlayerException: if the player or character wasn't found.
    :raises HiddenProfileException: if the player has chosen to hide their profile.
    """
    player_uuid = common.utils.misc.format_uuid(player_uuid, dashed=True)
    try:
        data = await session.get(f"/player/{player_uuid}/characters/{character_uuid}/abilities", rate_limit=_player_rate_limit)
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 400 or ex.status == 404:
            raise UnknownPlayerException(f'Player {player_uuid} or character with uuid {character_uuid} not found.')
        elif ex.status == 403:
            raise HiddenProfileException(f'{player_uuid} has hidden their profile.')
        else:
            raise ex

    return [AbilityNode.from_json(node) for node in data]


@alru_cache(ttl=30)
async def _online_players(identifier: PlayerIdentifier = PlayerIdentifier.USERNAME) -> dict:
    try:
        return await session.get(f"/player", identifier=identifier, rate_limit=_player_rate_limit)
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 524:
            time.sleep(1)
            return await session.get(f"/player", identifier=identifier, rate_limit=_player_rate_limit)
        else:
            raise ex


async def player_list(identifier: PlayerIdentifier = PlayerIdentifier.USERNAME) -> dict[str, str]:
    """
    Return a dictionary of players mapped to the world they are on.
    :param identifier: Must be either 'username' or 'uuid'. Indicates what the player key in the result should be.
    """
    return (await _online_players(identifier=identifier))['players']


async def player_count() -> int:
    """
    Return the number of players online.
    """
    return (await _online_players())['total']


def calculate_remaining_requests():
    return _player_rate_limit.calculate_remaining_calls()


def ratelimit_reset_time():
    return _player_rate_limit.get_time_until_reset()
