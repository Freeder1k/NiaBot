import dataclasses
import json
import os

import aiohttp.client_exceptions
from discord import Client
from discord.ext import tasks

import handlers.logging
import handlers.nerfuria.logging
import handlers.nerfuria.logging
import handlers.rateLimit
from wrappers import botConfig, minecraftPlayer
from wrappers.api.wynncraft.v3 import guild, types

_guild: types.GuildStats = None

try:
    if os.path.exists(f"{botConfig.GUILD_NAME}.json"):
        with open(f"{botConfig.GUILD_NAME}.json", 'r') as _f:
            _guild = types.GuildStats.from_json(json.load(_f))
except Exception as e:
    handlers.logging.error(
        f"Failed to load stored guild stats. Delete the file if this happens after an update. {e}")


async def _store_guild():
    with open(f"{botConfig.GUILD_NAME}.json", "w") as f:
        json.dump(dataclasses.asdict(_guild), f, indent=4)


async def _log_member_updates(client: Client, guild_now: types.GuildStats):
    members_prev = {uuid.replace("-", "").lower() for uuid in _guild.members.all.keys()}
    members_now = {uuid.replace("-", "").lower() for uuid in guild_now.members.all.keys()}

    joined_uuids = members_now - members_prev
    left_uuids = members_prev - members_now

    joined = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(joined_uuids))}
    left = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(left_uuids))}

    for uuid in joined_uuids:
        await handlers.nerfuria.logging.log_member_join(client, joined.get(uuid, '*unknown*'), uuid)
    for uuid in left_uuids:
        await handlers.nerfuria.logging.log_member_leave(client, left.get(uuid, '*unknown*'), uuid)


@tasks.loop(minutes=10, reconnect=True)
async def update_guild(client: Client):
    try:
        global _guild

        guild_now = await guild.stats(name=botConfig.GUILD_NAME)

        if _guild is not None:
            await _log_member_updates(client, guild_now)

        _guild = guild_now
        await _store_guild()
    except Exception as e:
        await handlers.logging.error(exc_info=e)
        raise e


update_guild.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
