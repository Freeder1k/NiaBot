import dataclasses
import json
import os

import aiohttp.client_exceptions
from discord import Client, TextChannel, Embed
from discord.ext import tasks

import handlers.logging
import handlers.rateLimit
import utils.misc
from handlers import serverConfig
from wrappers import botConfig, minecraftPlayer
from wrappers.api.wynncraft.v3 import guild, types
from wrappers.storage import guildMemberLogData

_guild: types.GuildStats = None

try:
    if os.path.exists(f"{botConfig.GUILD_NAME}.json"):
        with open(f"{botConfig.GUILD_NAME}.json", 'r') as _f:
            _guild = types.GuildStats.from_json(json.load(_f))
except Exception as e:
    handlers.logging.log_error(
        f"Failed to load stored guild stats. Delete the file if this happens after an update. {e}")


async def _store_guild():
    with open(f"{botConfig.GUILD_NAME}.json", "w") as f:
        json.dump(dataclasses.asdict(_guild), f, indent=4)


# TODO refactor duplicate log code with onlineplayers.py
async def _check_member_updates(client: Client, guild_now: types.GuildStats):
    members_prev = {uuid.replace("-", "").lower() for uuid in _guild.members.all.keys()}
    members_now = {uuid.replace("-", "").lower() for uuid in guild_now.members.all.keys()}

    joined_uuids = members_now - members_prev
    left_uuids = members_prev - members_now

    channel = client.get_channel(serverConfig.get_log_channel_id(botConfig.GUILD_DISCORD))
    if not isinstance(channel, TextChannel):
        print(channel)
        handlers.logging.log_error("Log channel for guild server is not text channel!")
        return

    perms = channel.permissions_for(channel.guild.me)
    if not perms.send_messages and perms.embed_links:
        print(channel)
        handlers.logging.log_error("Missing perms for log channel for guild server!")
        return

    joined = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(joined_uuids))}
    left = {p.uuid: p.name for p in await minecraftPlayer.get_players(uuids=list(left_uuids))}

    embeds = []
    for uuid in joined_uuids:
        em = Embed(
            title=f"**{joined.get(uuid, '*unknown*')} has joined the guild**",
            color=botConfig.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {utils.misc.format_uuid(uuid)}")
        embeds.append(em)
        await guildMemberLogData.log(guildMemberLogData.LogEntryType.MEMBER_JOIN,
                                     f"{joined.get(uuid, '*unknown*')} has joined the guild",
                                     uuid)
    for uuid in left_uuids:
        em = Embed(
            title=f"**{left.get(uuid, '*unknown*')} has left the guild**",
            color=botConfig.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {utils.misc.format_uuid(uuid)}")
        embeds.append(em)
        await guildMemberLogData.log(guildMemberLogData.LogEntryType.MEMBER_LEAVE,
                                     f"{left.get(uuid, '*unknown*')} has left the guild",
                                     uuid)

    if len(embeds) > 0:
        for i in range(0, len(embeds), 10):
            await channel.send(embeds=embeds[i:i + 10])


@tasks.loop(minutes=1, reconnect=True)
async def update_guild(client: Client):
    try:
        global _guild

        guild_now = await guild.stats(name=botConfig.GUILD_NAME)

        if _guild is not None:
            await _check_member_updates(client, guild_now)

        _guild = guild_now
        await _store_guild()
    except Exception as e:
        await handlers.logging.log_exception(e)
        raise e


update_guild.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
