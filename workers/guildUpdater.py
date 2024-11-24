import dataclasses
import json
import os
from collections.abc import Collection

from discord.ext import tasks

import common.api.rateLimit
import common.logging
import common.logging
import common.logging
from common.api.wynncraft.v3 import guild
from common.guildLogger import GuildLogger
from common.types.wynncraft import GuildStats
from common.utils import minecraftPlayer
from workers import usernameUpdater
from common.utils.misc import format_uuid

_guilds: dict[str, GuildStats | None] = {}
_active_guilds: list[str] = []
_guild_loggers: dict[str, GuildLogger] = {}


class NameChangeLogger(usernameUpdater.NameChangeSubscriber):
    def __init__(self, guild_name: str):
        self.guild_name = guild_name

    async def name_changed(self, uuid: str, prev_name: str, new_name: str):
        try:
            g = await guild.stats(name=self.guild_name)
        except Exception as e:
            common.logging.error(f"Name change logger failed to fetch guild data for bot guild {self.guild_name}!", e)
            return

        if format_uuid(uuid, dashed=True) not in g.members.all:
            return

        await _guild_loggers[self.guild_name].log_member_name_change(uuid, prev_name, new_name)


def _load_guilds():
    try:
        if os.path.exists(f"data/guilds.json"):
            with open(f"data/guilds.json", 'r') as _f:
                global _guilds
                _guilds = {name: GuildStats.from_json(data) for name, data in json.load(_f).items()}
    except Exception as e:
        common.logging.error("Failed to load stored guild stats.", exc_info=e)


def _store_guilds():
    with open(f"data/guilds.json", "w") as f:
        json.dump({name: dataclasses.asdict(data) for name, data in _guilds.items()}, f, indent=4)


async def _get_players(uuids: Collection[str]) -> dict[str, str]:
    players = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(uuids))}

    if len(players) != len(uuids):
        missing = set(uuids) - {uuid.replace("-", "").lower() for uuid in players}
        players.update({uuid: uuid for uuid in missing})

    return players


async def _get_member_updates(guild_prev: GuildStats, guild_now: GuildStats) -> tuple[dict[str, str], dict[str, str]]:
    members_prev = {uuid.replace("-", "").lower() for uuid in guild_prev.members.all.keys()}
    members_now = {uuid.replace("-", "").lower() for uuid in guild_now.members.all.keys()}

    joined_uuids = members_now - members_prev
    left_uuids = members_prev - members_now

    joined = await _get_players(joined_uuids)
    left = await _get_players(left_uuids)

    return joined, left


def add_guild(name: str, guild_logger: GuildLogger):
    """
    Add a guild to the guild updater.

    :param name: The name of the guild.
    :param guild_logger: The logger to use for this guild.
    """
    _active_guilds.append(name)
    _guild_loggers[name] = guild_logger

    usernameUpdater.subscribe(NameChangeLogger(name))

    if _guilds == {}:
        _load_guilds()

    if name not in _guilds:
        _guilds[name] = None


def remove_guild(name: str):
    """
    Remove a guild from the guild updater.

    :param name: The name of the guild.
    """
    _active_guilds.remove(name)
    _guild_loggers.pop(name)


async def _update_guild(name: str):
    try:
        try:
            guild_now = await guild.stats(name=name)
        except guild.UnknownGuildException:
            common.logging.error(f"Guild {name} not found. Removing this guild from update loop.")
            _active_guilds.remove(name)
            return

        if _guilds[name] is not None:
            joined, left = await _get_member_updates(_guilds[name], guild_now)

            guild_logger = _guild_loggers[guild_now.name]

            for uuid, pname in joined.items():
                await guild_logger.log_member_join(pname, uuid)
            for uuid, pname in left.items():
                await guild_logger.log_member_leave(pname, uuid)

        _guilds[name] = guild_now
    except common.api.rateLimit.RateLimitException:
        pass
    except Exception as e:
        await common.logging.error(exc_info=e)
        raise e


@tasks.loop(seconds=601, reconnect=True)
async def guild_updater():
    """
    Update guild information every 10 minutes. Use the `add_guild` function to add guilds to the updater.
    """
    exc_count = 0
    for name in _active_guilds:
        try:
            await _update_guild(name)
        except Exception:
            common.logging.error(f"Failed to update guild {name}.", exc_info=True)
            exc_count += 1

    if exc_count >= len(_active_guilds):
        raise Exception("All guild updates failed.")

    _store_guilds()


guild_updater.add_exception_type(Exception)
