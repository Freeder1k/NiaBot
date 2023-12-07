import asyncio
from queue import Queue

import aiohttp.client_exceptions
from discord import Client, TextChannel, Embed
from discord.ext import tasks

import handlers.logging
import handlers.rateLimit
import utils.misc
import wrappers.api
import wrappers.api.minecraft
import wrappers.api.wynncraft.guild
import wrappers.api.wynncraft.network
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.session
import wrappers.storage
import wrappers.storage.playerTrackerData
import wrappers.storage.usernameData
from handlers import serverConfig
from niatypes.dataTypes import MinecraftPlayer
from wrappers import botConfig
from wrappers.api.wynncraft.v3.types import PlayerStats
from wrappers.storage import guildMemberLogData

_online_players: set[str] = set()
_unknown_players: Queue[str] = Queue()
_players_to_track: Queue[str] = Queue()
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

    prev_names_dict = {p.uuid: p.name for p in prev_names}

    guild = await wrappers.api.wynncraft.v3.guild.stats(name=botConfig.GUILD_NAME)
    guild_members = {uuid.replace("-", "") for uuid in guild.members.all.keys()}
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
        em.set_footer(text=f"UUID: {utils.misc.format_uuid(player.uuid)}")
        embeds.append(em)
        await guildMemberLogData.log(guildMemberLogData.LogEntryType.MEMBER_NAME_CHANGE,
                                     f"Name changed: {prev_names_dict.get(player.uuid, '*unknown*')} -> {player.name}",
                                     player.uuid)

    if len(embeds) > 0:
        for i in range(0, len(embeds), 10):
            await channel.send(embeds=embeds[i:i + 10])


async def _fetch_and_update_username(username: str):
    p = await wrappers.api.minecraft.get_player(username=username)
    prev_p = None

    if p is None:
        handlers.logging.log_debug(f"{username} is not a minecraft name but online on wynncraft!")
    else:
        prev_p = await wrappers.storage.usernameData.update(p.uuid, p.name)

    return p, prev_p


async def _update_usernames(client: Client):
    if _unknown_players.qsize() == 0:
        return

    max_calls = wrappers.api.minecraft._mojang_rate_limit.calculate_remaining_calls()
    calls = min(max_calls, _unknown_players.qsize())
    if calls >= 10:
        handlers.logging.log_debug(f"Updating {calls} minecraft usernames.")
    # TODO use usernames endpoint if a lot of usernames

    res = await asyncio.gather(*(_fetch_and_update_username(_unknown_players.get()) for _ in range(0, calls)))

    updated_names = [r[0] for r in res if r[0] is not None]
    prev_names = [r[1] for r in res if r[1] is not None]

    await _notify_guild_member_name_changes(client, prev_names, updated_names)


async def _record_stats(username: str):
    stats = None
    try:
        stats: PlayerStats = await wrappers.api.wynncraft.v3.player.stats(player=username)
        if stats.uuid is None:
            return  # TODO do something about multiple matching names
        await wrappers.storage.playerTrackerData.add_record(stats)
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
        p = await wrappers.storage.usernameData.get_player(username=username)
        if p is None:
            handlers.logging.log_debug(f"Couldn't get stats of player {username}")
            return
        try:
            uuid = utils.misc.get_dashed_uuid(p.uuid)
            stats = await wrappers.api.wynncraft.v3.player.stats(player=uuid)
            await wrappers.storage.playerTrackerData.add_record(stats)
        except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
            handlers.logging.log_debug(f"Couldn't get stats of player {username}")
    except Exception as e:
        handlers.logging.log_error(username, stats)
        raise e


async def _track_stats():
    if _players_to_track.qsize() == 0:
        return

    max_calls = min(200, wrappers.api.wynncraft.v3.session.calculate_remaining_requests())
    calls = min(max_calls, _players_to_track.qsize())
    if calls >= 50:
        handlers.logging.log_debug(f"Recording {calls} player's stats.")

    await asyncio.gather(*(_record_stats(_players_to_track.get()) for _ in range(0, calls)))


@tasks.loop(seconds=61, reconnect=True)
async def update_players(client: Client):
    try:
        global _online_players, _players_to_track
        prev_online_players = _online_players
        # TODO API v3 broken, still use old api here
        # _online_players = (await wrappers.api.wynncraft.v3.player.player_list()).keys()
        _online_players = await wrappers.api.wynncraft.network.online_players()
        joined_players = _online_players - prev_online_players
        left_players = prev_online_players - _online_players

        known_names = {p.name for p in await wrappers.storage.usernameData.get_players(usernames=list(joined_players))}
        for name in joined_players:
            if name not in known_names:
                _unknown_players.put(name)

        await _update_usernames(client)

        for name in left_players:
            _players_to_track.put(name)
        await _track_stats()

    except Exception as ex:
        await handlers.logging.log_exception(ex)
        await asyncio.sleep(60)  # Wait here so the loop reconnect doesn't trigger a RateLimitException instantly
        raise ex


update_players.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    handlers.rateLimit.RateLimitException
)
