import aiohttp.client_exceptions
from async_lru import alru_cache

from niatypes.wynncraft.v3.player import PlayerStats, CharacterShort, AbilityMap
from wrappers.api.wynncraft.v3 import session


class UnknownPlayerException(Exception):
    pass


class HiddenProfileException(Exception):
    pass


@alru_cache(ttl=120)
async def stats(player: str, full_result: bool = False) -> PlayerStats:
    """
    Request public statistical information about the specified player.
    :param player: Either the username or the uuid in dashed form (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    :param full_result: If True, the character list is included in the result.
    :returns: A Stats object.
    :raises UnknownPlayerException: if the player wasn't found.
    """
    if full_result:
        params = {"fullResult": str(full_result)}
    else:
        params = {}

    data = await session.get(f"/player/{player}", **params)

    if len(data) == 0 or data['username'] is None:
        raise UnknownPlayerException(f'Player {player} not found.')

    return PlayerStats.from_json(data)


@alru_cache(ttl=120)
async def characters(player: str) -> dict[str, CharacterShort]:
    """
    Request a list of short info on the specified players characters.
    :param player: Either the username or the uuid in dashed form (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    :returns: A dictionary of character_uuids mapped to a CharacterShort object.
    :raises UnknownPlayerException: if the player wasn't found.
    """
    try:
        data = await session.get(f"/player/{player}/characters")
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 400:
            raise UnknownPlayerException(f'Player {player} not found.')
        else:
            raise ex

    return {uuid: CharacterShort.from_json(data) for uuid, data in data.items()}


@alru_cache(ttl=600)
async def abilities(player: str, character_uuid: str) -> AbilityMap:
    """
    Request the ability map of the specified character.
    :param player: Either the username or the uuid in dashed form (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    :param character_uuid: The character uuid.
    :returns: An AbilityMap object.
    :raises UnknownPlayerException: if the player or character wasn't found.
    :raises HiddenProfileException: if the player has choses to hide their profile.
    """
    try:
        data = await session.get(f"/player/{player}/characters/{character_uuid}/abilities")
    except aiohttp.client_exceptions.ClientResponseError as ex:
        if ex.status == 400:
            raise UnknownPlayerException(f'Player {player} or character with uuid {character_uuid} not found.')
        elif ex.status == 403:
            raise HiddenProfileException(f'{player} has hidden their profile.')
        else:
            raise ex

    return AbilityMap.from_json(data)

@alru_cache(ttl=30)
async def player_list() -> dict:
    return await session.get(f"/player")

