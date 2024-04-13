import re
from datetime import datetime, timedelta
from typing import Iterable

import discord.utils

import wrappers.api.wynncraft.v3.guild
from niatypes.constants import time_units_map, seasons
from niatypes.dataTypes import WynncraftGuild
from utils.misc import pluralize

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


_rel_time_pattern = re.compile(r"^(\d+)(.*)")
_season_pattern = re.compile(r"^s(\d+)")


class Timeframe:
    """
    Represents a timeframe (start and end date and a string representation).
    """

    def __init__(self, start: datetime, end: datetime, str_repr: str = None):
        self.start = start
        self.end = end
        if str_repr is None:
            self.str_repr = discord.utils.format_dt(start, "f") + " - " + discord.utils.format_dt(end, "f")
        else:
            self.str_repr = str_repr

    @classmethod
    def from_timeframe_str(cls, timeframe: str):
        """
        Create a Timeframe object from a string representation.
        Valid formats:
        - ``<number><unit>`` (e.g. ``5days``) for relative time since now
        - ``s<number>`` (e.g. ``s1``) for a specific season number
        """
        match = _rel_time_pattern.fullmatch(timeframe)
        if match is not None:
            num = int(match.group(0))
            unit = match.group(1)
            if unit not in time_units_map:
                raise ValueError(f"Invalid time unit: ``{unit}``")
            unit = time_units_map[unit]
            if unit == "months":
                unit = "days"
                num *= 31
            elif unit == "years":
                unit = "days"
                num *= 365

            return cls(
                datetime.utcnow() - timedelta(**{unit: num}),
                datetime.utcnow(),
                f"last {num} {pluralize(num, unit[:-1])}"
            )

        match = _season_pattern.fullmatch(timeframe)
        if match is not None:
            season = int(match.group(1))
            if season >= len(seasons):
                raise ValueError(f"Invalid season number: ``{match.group(1)}``")
            return cls(seasons[season][0], seasons[season][1], f"season {season}")

        raise ValueError(f"Invalid timeframe format: ``{timeframe}``")

    def __str__(self):
        return self.str_repr
