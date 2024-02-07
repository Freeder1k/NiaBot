import asyncio

import aiohttp.client_exceptions
from discord import Client
from discord.ext import tasks

import handlers.logging
import handlers.nerfuria.logging
import handlers.nerfuria.logging
import handlers.rateLimit
import wrappers.api
import wrappers.api.minecraft
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.session
import wrappers.storage
import wrappers.storage.playerTrackerData
import wrappers.storage.usernameData
from niatypes.dataTypes import MinecraftPlayer
from workers.queueWorker import QueueWorker
from wrappers import botConfig

_online_players: set[str] = set()
_updated_players: list[tuple[MinecraftPlayer, MinecraftPlayer]] = []
_error_count = 0
_worker = QueueWorker(delay=0.1)


async def _notify_guild_member_name_changes(client: Client):
    await _worker.join()

    if len(_updated_players) == 0:
        return

    try:
        guild = await wrappers.api.wynncraft.v3.guild.stats(name=botConfig.GUILD_NAME)
    except Exception as e:
        handlers.logging.error("Failed to fetch guild data for bot guild!", e)
        return

    prev_names, updated_names = zip(*_updated_players)
    _updated_players.clear()

    prev_names_dict = {p.uuid: p.name for p in prev_names if p is not None}

    guild_members = {uuid.replace("-", "") for uuid in guild.members.all.keys()}
    updated_guild_members = [p for p in updated_names if p.uuid in guild_members]

    for player in updated_guild_members:
        await handlers.nerfuria.logging.log_member_name_change(client,
                                                               player.uuid,
                                                               prev_names_dict.get(player.uuid, "*unknown*"),
                                                               player.name)


async def _fetch_and_update_username(username: str):
    if wrappers.api.minecraft._mojang_rate_limit.calculate_remaining_calls() < 10:
        wait_time = wrappers.api.minecraft._mojang_rate_limit.get_time_until_next_free()
        await asyncio.sleep(wait_time + 1)

    try:
        p = await wrappers.api.minecraft.get_player(username=username)
    except handlers.rateLimit.RateLimitException as e:
        handlers.logging.error("Rate limit reached for mojang api!", e)
        _worker.put(_fetch_and_update_username, username)
        return

    if p is None:
        handlers.logging.debug(f"{username} is not a minecraft name but online on wynncraft!")
    else:
        prev_p = await wrappers.storage.usernameData.update(p.uuid, p.name)
        _updated_players.append((prev_p, p))


@tasks.loop(seconds=61, reconnect=True)
async def _update_usernames(client: Client):
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = (await wrappers.api.wynncraft.v3.player.player_list(identifier='username')).keys()

        joined_players = _online_players - prev_online_players

        known_names = {p.name for p in await wrappers.storage.usernameData.get_players(usernames=list(joined_players))}

        updates = len(
            [_worker.put(_fetch_and_update_username, name) for name in joined_players if name not in known_names])

        if updates >= 10:
            handlers.logging.debug(f"Updating {updates} minecraft usernames.")

        asyncio.create_task(_notify_guild_member_name_changes(client))
    except handlers.rateLimit.RateLimitException:
        pass
    except Exception as ex:
        await handlers.logging.error(exc_info=ex)
        raise ex


_update_usernames.add_exception_type(
    aiohttp.client_exceptions.ClientError
)


def start(client: Client):
    _update_usernames.start(client=client)
    _worker.start()
    handlers.logging.info("Username updater workers started.")


def stop():
    _worker.stop()
    _update_usernames.stop()
