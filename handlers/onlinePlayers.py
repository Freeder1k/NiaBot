import asyncio
from queue import Queue

import aiohttp.client_exceptions
from discord import Client, TextChannel, Embed
from discord.ext import tasks

import handlers.logging
import handlers.rateLimit
import wrappers.api
import wrappers.api.minecraft
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.network
import wrappers.storage
import wrappers.storage.usernameData
from handlers import serverConfig
from niatypes.dataTypes import MinecraftPlayer
from wrappers import botConfig
from wrappers.storage import guildMemberLogData

_online_players: set[str] = set()
_unknown_players: Queue[str] = Queue()
_reservation_id: int = wrappers.api.minecraft._usernames_rate_limit.reserve(20)


async def _notify_guild_member_name_changes(client: Client, prev_names: list[MinecraftPlayer],
                                            updated_names: list[MinecraftPlayer]):
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

    prev_names_dict = {p.uuid: p.name for p in prev_names if p is not None}

    guild = await wrappers.api.wynncraft.guild.stats(botConfig.GUILD_NAME)
    guild_members = {m.uuid.replace("-", ""): m.name for m in guild.members}
    updated_guild_members = []
    for player in updated_names:
        if player.uuid in guild_members:
            updated_guild_members.append(player)

    embeds = []
    for player in updated_guild_members:
        em = Embed(
            title=f"Name changed: **{prev_names_dict.get(player.uuid, '*unknown*')} -> {player.name}**",
            color=botConfig.DEFAULT_COLOR,
        )
        em.set_footer(text=f"UUID: {wrappers.api.minecraft.format_uuid(player.uuid)}")
        embeds.append(em)
        await guildMemberLogData.log(guildMemberLogData.LogEntryType.MEMBER_NAME_CHANGE,
                                     f"Name changed: {prev_names_dict.get(player.uuid, '*unknown*')} -> {player.name}",
                                     player.uuid)

    if len(embeds) > 0:
        for i in range(0, len(embeds), 10):
            await channel.send(embeds=embeds[i:i + 10])


async def _update_usernames(client: Client):
    if _unknown_players.empty():
        return

    prev_names = []
    updated_names = []

    # utils.logging.log_debug(f"Updating {min(_unknown_players.qsize(), 200)} minecraft usernames.")

    for i in range(0, min((_unknown_players.qsize() + 9) // 10, 20)):
        unknown_players_batch = [_unknown_players.get() for _ in range(0, min(_unknown_players.qsize(), 10))]

        res = await wrappers.api.minecraft.get_players_from_usernames(unknown_players_batch,
                                                                      reservation_id=_reservation_id)
        prev_names += await asyncio.gather(
            *(wrappers.storage.usernameData.update(uuid, name) for uuid, name in res))

        for name in unknown_players_batch:
            if not any(name == t_name for _, t_name in res):
                handlers.logging.log_debug(f"{name} not a minecraft name but online on wynncraft!")

        updated_names += res

    await _notify_guild_member_name_changes(client, prev_names, updated_names)

    wrappers.api.minecraft._usernames_rate_limit.free(_reservation_id)


@tasks.loop(minutes=1, reconnect=True)
async def update_players(client: Client):
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = await wrappers.api.wynncraft.network.online_players()
        joined_players = _online_players - prev_online_players

        known_names = {p.name for p in await wrappers.storage.usernameData.get_players(usernames=list(joined_players))}
        for name in joined_players:
            if name not in known_names:
                _unknown_players.put(name)

        await _update_usernames(client)

    except Exception as ex:
        await handlers.logging.log_exception(ex)
        await asyncio.sleep(60)  # Wait here so the loop reconnect doesn't trigger a RateLimitException directly
        raise ex


update_players.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
