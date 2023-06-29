import dataclasses
import json
import os

import aiohttp.client_exceptions
from discord import Client, TextChannel, Embed
from discord.ext import tasks

import api.minecraft
import api.rateLimit
import api.wynncraft.guild
import botConfig
import player
import serverConfig
import utils.logging
import utils.misc

_guild: api.wynncraft.guild.Stats = None


async def _load_stored():
    global _guild
    if os.path.exists(f"{botConfig.GUILD_NAME}.json"):
        with open(f"{botConfig.GUILD_NAME}.json", 'r') as f:
            _guild = utils.misc.dataclass_from_dict(api.wynncraft.guild.Stats, json.load(f))


async def _store():
    with open(f"{botConfig.GUILD_NAME}.json", "w") as f:
        json.dump(dataclasses.asdict(_guild), f, indent=4)


async def _notify_member_updates(client: Client, joined_uuids: set[str], left_uuids: set[str]):
    channel = client.get_channel(serverConfig.get_log_channel_id(botConfig.GUILD_DISCORD))
    if not isinstance(channel, TextChannel):
        print(channel)
        utils.logging.elog("Log channel for guild server is not text channel!")
        return

    embed = Embed(
        title="Member updates:",
        color=botConfig.DEFAULT_COLOR
    )

    joined = {p.uuid: p.name for p in await player.get_players(uuids=list(joined_uuids))}
    left = {p.uuid: p.name for p in await player.get_players(uuids=list(left_uuids))}

    joined_names = [joined.get(uuid, api.minecraft.format_uuid(uuid)) for uuid in joined_uuids]
    left_names = [left.get(uuid, api.minecraft.format_uuid(uuid)) for uuid in left_uuids]

    if len(joined_names) > 0:
        embed.add_field(name="Joins:", value='```\n' + '\n'.join(joined_names) + '```', inline=True)
    if len(left_names) > 0:
        embed.add_field(name="Leaves:", value='```\n' + '\n'.join(left_names) + '```', inline=True)

    if len(joined_names) > 0 or len(left_names) > 0:
        await channel.send(embed=embed)


@tasks.loop(minutes=1, reconnect=True)
async def update_guild(client: Client):
    global _guild
    if _guild is None:
        await _load_stored()

    if _guild is None:
        _guild = await api.wynncraft.guild.stats(botConfig.GUILD_NAME)
        await _store()
        return

    guild_now = await api.wynncraft.guild.stats(botConfig.GUILD_NAME)

    members_prev = {m.uuid.replace("-", "").lower() for m in _guild.members}
    members_now = {m.uuid.replace("-", "").lower() for m in guild_now.members}

    joined = members_now - members_prev
    left = members_prev - members_now

    await _notify_member_updates(client, joined, left)

    _guild = guild_now
    await _store()


update_guild.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    api.rateLimit.RateLimitException
)
