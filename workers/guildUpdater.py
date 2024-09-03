import dataclasses
import json
import os

import aiohttp.client_exceptions
from discord.ext import tasks

import common.api.rateLimit
import common.logging
import common.logging
import common.logging
from common.api.wynncraft.v3 import guild
from common.guildLogger import GuildLogger
from common.types.wynncraft import GuildStats
from common.utils import minecraftPlayer


def load_guilds():
    try:
        if os.path.exists(f"data/guilds.json"):
            with open(f"data/guilds.json", 'r') as _f:
                return {name: GuildStats.from_json(data) for name, data in json.load(_f).items()}
    except Exception as e:
        common.logging.error("Failed to load stored guild stats.", exc_info=e)


_guilds: dict[str, GuildStats | None] = load_guilds()
_active_guilds: list[str] = []
_guild_loggers: dict[str, GuildLogger] = {}


def _store_guilds():
    with open(f"data/guilds.json", "w") as f:
        json.dump({name: dataclasses.asdict(data) for name, data in _guilds.items()}, f, indent=4)


async def _log_member_updates(guild_prev: GuildStats, guild_now: GuildStats):
    members_prev = {uuid.replace("-", "").lower() for uuid in guild_prev.members.all.keys()}
    members_now = {uuid.replace("-", "").lower() for uuid in guild_now.members.all.keys()}

    joined_uuids = members_now - members_prev
    left_uuids = members_prev - members_now

    joined = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(joined_uuids))}
    left = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(left_uuids))}

    guild_logger = _guild_loggers[guild_now.name]

    for uuid in joined_uuids:
        await guild_logger.log_member_join(joined.get(uuid, '*unknown*'), uuid)
    for uuid in left_uuids:
        await guild_logger.log_member_leave(left.get(uuid, '*unknown*'), uuid)


def add_guild(name: str, guild_logger: GuildLogger):
    _active_guilds.append(name)
    _guild_loggers[name] = guild_logger
    if name not in _guilds:
        _guilds[name] = None


async def _update_guild(name: str):
    try:
        try:
            guild_now = await guild.stats(name=name)
        except guild.UnknownGuildException:
            common.logging.error(f"Guild {name} not found. Removing this guild from update loop.")
            _active_guilds.remove(name)
            return

        if _guilds[name] is not None:
            await _log_member_updates(guild_now)

        _guilds[name] = guild_now
    except common.api.rateLimit.RateLimitException:
        pass
    except Exception as e:
        await common.logging.error(exc_info=e)
        raise e


@tasks.loop(seconds=601, reconnect=True)
async def guild_updater():
    exc_count = 0
    for name in _active_guilds:
        try:
            await _update_guild(name)
        except Exception:
            exc_count += 1

    if exc_count >= len(_guilds):
        raise Exception("All guild updates failed.")

    _store_guilds()


guild_updater.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
