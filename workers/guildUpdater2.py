import dataclasses
import json
import os

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import handlers.nerfuria.logging2
import handlers.nerfuria.logging2
import handlers.rateLimit
from wrappers import botConfig, minecraftPlayer
from wrappers.api.wynncraft.v3 import guild, types

_guild: types.GuildStats = None

try:
    if os.path.exists(f"data/{botConfig.GUILD_NAME2}.json"):
        with open(f"data/{botConfig.GUILD_NAME2}.json", 'r') as _f:
            _guild = types.GuildStats.from_json(json.load(_f))
except Exception as e:
    handlers.logging.error("Failed to load stored guild stats.", exc_info=e)


async def _store_guild():
    with open(f"data/{botConfig.GUILD_NAME2}.json", "w") as f:
        json.dump(dataclasses.asdict(_guild), f, indent=4)


async def _log_member_updates(guild_now: types.GuildStats):
    members_prev = {uuid.replace("-", "").lower() for uuid in _guild.members.all.keys()}
    members_now = {uuid.replace("-", "").lower() for uuid in guild_now.members.all.keys()}

    joined_uuids = members_now - members_prev
    left_uuids = members_prev - members_now

    joined = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(joined_uuids))}
    left = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(left_uuids))}

    for uuid in joined_uuids:
        await handlers.nerfuria.logging2.log_member_join(joined.get(uuid, '*unknown*'), uuid)
    for uuid in left_uuids:
        await handlers.nerfuria.logging2.log_member_leave(left.get(uuid, '*unknown*'), uuid)


@tasks.loop(seconds=601, reconnect=True)
async def update_guild():
    try:
        global _guild

        try:
            guild_now = await guild.stats(name=botConfig.GUILD_NAME2)
        except guild.UnknownGuildException:
            handlers.logging.error(f"Guild {botConfig.GUILD_NAME2} not found. Disabling guild update loop.")
            update_guild.stop()
            return

        if _guild is not None:
            await _log_member_updates(guild_now)

        _guild = guild_now
        await _store_guild()
    except handlers.rateLimit.RateLimitException:
        pass
    except Exception as e:
        await handlers.logging.error(exc_info=e)
        raise e


update_guild.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)
