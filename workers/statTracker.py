import asyncio
import os

import aiohttp.client_exceptions
from discord.ext import tasks

import common.api
import common.api.minecraft
import common.api.rateLimit
import common.api.wynncraft.v3.guild
import common.api.wynncraft.v3.player
import common.api.wynncraft.v3.session
import common.logging
import common.storage.playerTrackerData
import common.storage.usernameData
import workers.usernameUpdater
from common.api.wynncraft.v3 import guild
from common.types.dataTypes import MinecraftPlayer
from common.types.enums import PlayerIdentifier
from workers.queueWorker import QueueWorker
from workers.guildUpdater import get_active_guilds

from dotenv import load_dotenv
load_dotenv()

_online_players: set[str] = set()
_worker = QueueWorker(delay=0.01)

_first_update = True


async def _record_stats(uuid: str, tries: int, api_key: str=None):
    if common.api.wynncraft.v3.player.calculate_remaining_requests() < 10:
        wait_time = common.api.wynncraft.v3.player.ratelimit_reset_time()
        await asyncio.sleep(wait_time + 1)

    stats = None
    try:
        stats = await common.api.wynncraft.v3.player.stats(uuid=uuid, api_key=api_key)
        player = MinecraftPlayer(uuid=stats.uuid, name=stats.username)
        await workers.usernameUpdater.update_username(player)
        if stats.globalData is None:
            return # Main access set to private, no stats available.
        await common.storage.playerTrackerData.add_record(stats)
    except common.api.wynncraft.v3.player.UnknownPlayerException:
        common.logging.debug(f"Couldn't get stats of player with uuid {uuid}: Unknown player.")
    except aiohttp.client_exceptions.ClientResponseError as e:
        if e.status == 500:
            common.logging.warning(f"Error 500 for player with uuid: {uuid}")
        elif tries < 1:
            _worker.put_delayed(_record_stats, 30, uuid, tries + 1)
        else:
            common.logging.error(f"Client error in player stat tracker: uuid: {uuid}")
            raise e
    except Exception as e:
        common.logging.error(f"Exception in player stat tracker: uuid: {uuid}, stats: {stats}")
        raise e

async def _update_guild_members():
    for name in get_active_guilds():
        try:
            try:
                g = await guild.stats(name=name)
            except guild.UnknownGuildException:
                continue

            key = None
            if name == "Nerfuria":
                key = os.getenv('WYNN_NIA_API_KEY')

            for i, uuid in enumerate(g.members.all.keys()):
                _worker.put(_record_stats, uuid, 0, key)
        except Exception as e:
            await common.logging.error(exc_info=e)


@tasks.loop(seconds=31, reconnect=True)
async def _update_online():
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = set(
            (await common.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.UUID)).keys())

        joined_players = _online_players - prev_online_players
        left_players = prev_online_players - _online_players

        if len(prev_online_players) == 0:
            return
        for uuid in joined_players:
            _worker.put(_record_stats, uuid, 0)
        for uuid in left_players:
            _worker.put(_record_stats, uuid, 0)

        global _first_update
        if _first_update:
            await _update_guild_members()
            _first_update = False

        if _worker.qsize() >= 100:
            common.logging.debug(f"Tracking {len(joined_players) + len(left_players)}({_worker.qsize()}) player's stats.")
    except common.api.rateLimit.RateLimitException:
        pass
    except Exception as ex:
        await common.logging.error(exc_info=ex)
        raise ex


_update_online.add_exception_type(aiohttp.client_exceptions.ClientError, Exception)


def start():
    _update_online.start()
    _worker.start()
    common.logging.info("Stat Tracker worker started.")


def stop():
    _worker.stop()
    _update_online.stop()
