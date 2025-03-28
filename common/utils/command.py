import re
from datetime import datetime, timedelta
from typing import Iterable

import dateparser

import discord
import discord.utils
from discord.app_commands import Choice

import common.api.wynncraft.v3.guild
import common.storage
import common.storage.usernameData
import workers.guildIndexer
from common.types.constants import time_units_map, seasons
from common.types.dataTypes import MinecraftPlayer
from common.types.enums import PlayerStatsIdentifier
from common.types.wynncraft import WynncraftGuild
from common.utils import minecraftPlayer
from common.utils.misc import pluralize
import common.utils.minecraftPlayer

USERNAME_RE = re.compile(r'[0-9A-Za-z_]+')
UUID_RE = re.compile(r'[0-9a-f]+')
GUILD_RE = re.compile(r'[A-Za-z ]{1,30}')

_REL_TIME_RE = re.compile(r"^(\d+)(.*)")
_SEASON_RE = re.compile(r"^s(\d+)")


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
    if not GUILD_RE.fullmatch(guild_str) or len(guild_str) < 3:
        raise ValueError(f"Invalid guild name or tag ``{guild_str}``")

    possible_guilds: tuple[WynncraftGuild] = await common.api.wynncraft.v3.guild.find(guild_str)
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


async def parse_player(player_str: str) -> MinecraftPlayer:
    """
    Parse a player string into a MinecraftPlayer object.
    :param player_str: The player string to parse.
    :return: The MinecraftPlayer object.
    :raises ValueError: If the player string is invalid or the specified player doesn't exist.
    """
    if USERNAME_RE.fullmatch(player_str):
        p = await common.utils.minecraftPlayer.get_player(username=player_str)
    elif UUID_RE.fullmatch(player_str):
        p = await common.storage.usernameData.get_player(uuid=player_str)
    else:
        raise ValueError(f"Player must be a valid uuid or username: ``{player_str}``")

    if p is None:
        raise ValueError(f"Couldn't find player ``{player_str}``.")
    return p

def parse_datetime(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.
    :param date_str: The date string to parse.
    :return: The datetime object.
    :raises ValueError: If the date string is invalid.
    """
    value = dateparser.parse(date_str, settings={'TIMEZONE': 'UTC'})
    if value is None:
        raise ValueError(f"Invalid datetime: ``{date_str}``")
    return value


class Timeframe:
    """
    Represents a timeframe (start and end date and a string representation).
    """

    def __init__(self, start: datetime, end: datetime, comment: str = None):
        self.start = start
        self.end = end
        self.comment = comment

    @classmethod
    def from_timeframe_str(cls, timeframe: str):
        """
        Create a Timeframe object from a string representation.
        Valid formats:
        - ``<number><unit>`` (e.g. ``5days``) for relative time since now
        - ``s<number>`` (e.g. ``s1``) for a specific season number
        """
        match = _REL_TIME_RE.fullmatch(timeframe)
        if match is not None:
            num = int(match.group(1))
            unit = match.group(2)
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

        match = _SEASON_RE.fullmatch(timeframe)
        if match is not None:
            season = int(match.group(1))
            if season >= len(seasons):
                raise ValueError(f"Invalid season number: ``{match.group(1)}``")
            return cls(seasons[season][0], seasons[season][1], f"season {season}")

        raise ValueError(f"Invalid timeframe format: ``{timeframe}``")

    def __str__(self):
        return discord.utils.format_dt(self.start, "d") + " - " + discord.utils.format_dt(self.end, "d")


async def stats_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if len(current) == 0:
        return [Choice(name=stat, value=stat) for stat in PlayerStatsIdentifier if not stat.startswith("dungeon")] \
            + [Choice(name='dungeons_', value='dungeons_')]

    return [
               Choice(name=stat, value=stat)
               for stat in PlayerStatsIdentifier if current.lower() in stat.lower()
           ][0:25]


stats_choices = [
    Choice(name=stat, value=stat)
    for stat in [
        "playtime",
        "wars",
        "total_levels",
        "killed_mobs",
        "chests_found",
        "dungeons_total",
        "raids_total",
        "raids_notg",
        "raids_nol",
        "raids_tcc",
        "raids_tna",
        "completed_quests",
        "pvp_kills",
        "pvp_deaths"
    ]
]


async def player_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if len(current) < 3:
        return []
    return [
               Choice(name=p.name, value=p.name)
               for p in await common.storage.usernameData.find_players(current)
           ][0:25]


async def guild_autocomplete(
        interaction: discord.Interaction,
        current: str,
) -> list[Choice[str]]:
    if not GUILD_RE.fullmatch(current):
        return []

    matches = workers.guildIndexer.get_index().get(current.lower(), [])
    return [Choice(name=name, value=name) for name in matches][:25]


