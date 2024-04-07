import re
from typing import Iterable

import wrappers.api.wynncraft.v3.guild
from niatypes.dataTypes import WynncraftGuild

guild_re = re.compile(r'[A-Za-z ]{3,30}')


class AmbiguousGuildError(ValueError):
    """
    Multiple guilds match the same guild string.
    """

    def __init__(self, guild_str, guilds: Iterable[WynncraftGuild]):
        self.options = '\n'.join([f'- {g.name} [{g.tag}]' for g in guilds])
        super().__init__(f"Found multiple matches for ``{guild_str}``:\n{self.options}")


class UnknownGuildError(ValueError):
    """
    The specified guild doesn't exist.
    """

    def __init__(self, guild_str):
        super().__init__(f"Couldn't find guild ``{guild_str}``")


async def parse_guild(guild_str: str) -> WynncraftGuild:
    """
    Parse a guild string into a WynncraftGuild object.
    :param guild_str: The guild string to parse.
    :return: The WynncraftGuild object.
    :raises ValueError: If the guild string is invalid or the specified guild doesn't exist.
    :raises AmbiguousGuildError: If the guild string is ambiguous.
    """
    if not guild_re.fullmatch(guild_str):
        raise ValueError(f"Invalid guild name or tag ``{guild_str}``")

    possible_guilds: tuple[WynncraftGuild] = await wrappers.api.wynncraft.v3.guild.find(guild_str)
    if not possible_guilds:
        raise UnknownGuildError(guild_str)

    if len(possible_guilds) == 1:
        return possible_guilds[0]
    else:
        exact_matches = [g for g in possible_guilds if g.tag == guild_str or g.name == guild_str]
        if not exact_matches:
            raise AmbiguousGuildError(guild_str, possible_guilds)
        elif len(exact_matches) == 1:
            return exact_matches[0]
        else:
            raise AmbiguousGuildError(guild_str, exact_matches)
