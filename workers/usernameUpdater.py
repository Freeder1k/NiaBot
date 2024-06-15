import asyncio

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import handlers.nerfuria.logging
import handlers.nerfuria.logging2
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
from niatypes.enums import PlayerIdentifier
from workers.queueWorker import QueueWorker
from wrappers import botConfig

_online_players: set[str] = set()
_updated_players: list[tuple[MinecraftPlayer, MinecraftPlayer]] = []
_worker = QueueWorker(delay=0.5)


async def _log_name_changes():
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
        await handlers.nerfuria.logging.log_member_name_change(player.uuid,
                                                               prev_names_dict.get(player.uuid, "*unknown*"),
                                                               player.name)

    try:
        guild2 = await wrappers.api.wynncraft.v3.guild.stats(name=botConfig.GUILD_NAME2)
    except Exception as e:
        handlers.logging.error("Failed to fetch guild data for bot guild2!", e)
        return

    guild_members = {uuid.replace("-", "") for uuid in guild2.members.all.keys()}
    updated_guild_members = [p for p in updated_names if p.uuid in guild_members]

    for player in updated_guild_members:
        await handlers.nerfuria.logging2.log_member_name_change(player.uuid,
                                                               prev_names_dict.get(player.uuid, "*unknown*"),
                                                               player.name)


async def _fetch_and_update_usernames(usernames: list[str]):
    if wrappers.api.minecraft._mc_services_rate_limit.calculate_remaining_calls() < 2:
        wait_time = wrappers.api.minecraft._mc_services_rate_limit.get_time_until_next_free()
        await asyncio.sleep(wait_time + 1)

    try:
        players = await wrappers.api.minecraft.get_players(usernames=usernames)
    except handlers.rateLimit.RateLimitException as e:
        handlers.logging.error("Rate limit reached for mojang api!", e)
        wait_time = wrappers.api.minecraft._mc_services_rate_limit.get_time_until_next_free()
        print(wait_time)
        await asyncio.sleep(wait_time + 1)
        _worker.put(_fetch_and_update_usernames, usernames)
        return
    except aiohttp.client_exceptions.ClientError as e:
        handlers.logging.error("Failed usernames: ", usernames)
        await asyncio.sleep(60)
        _worker.put(_fetch_and_update_usernames, usernames)
        raise e

    for name in usernames:
        if name not in players:
            handlers.logging.debug(f"{name} is not a minecraft name but online on wynncraft!")

    for p in players.values():
        prev_p = await wrappers.storage.usernameData.update(p.uuid, p.name)
        _updated_players.append((prev_p, p))


@tasks.loop(seconds=61, reconnect=True)
async def _update_usernames():
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = (
            await wrappers.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.USERNAME)).keys()

        joined_players = _online_players - prev_online_players

        known_names = {p.name for p in await wrappers.storage.usernameData.get_players(usernames=list(joined_players))}
        unknown_names = [name for name in joined_players if name not in known_names]

        for i in range(0, len(unknown_names), 10):
            _worker.put(_fetch_and_update_usernames, unknown_names[i:i + 10])

        if len(unknown_names) >= 10:
            handlers.logging.debug(f"Updating {len(unknown_names)} minecraft usernames.")

        asyncio.create_task(_log_name_changes())
    except handlers.rateLimit.RateLimitException:
        pass
    except Exception as ex:
        await handlers.logging.error(exc_info=ex)
        raise ex


_update_usernames.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)


def start():
    _update_usernames.start()
    _worker.start()
    handlers.logging.info("Username updater workers started.")


def stop():
    _worker.stop()
    _update_usernames.stop()
