import asyncio

import aiohttp.client_exceptions
from discord.ext import tasks

import handlers.logging
import handlers.rateLimit
import wrappers.api
import wrappers.api.minecraft
import wrappers.api.wynncraft.v3.guild
import wrappers.api.wynncraft.v3.player
import wrappers.api.wynncraft.v3.session
import wrappers.storage
import wrappers.storage.playerTrackerData
import wrappers.storage.usernameData
from niatypes.enums import PlayerIdentifier
from workers.queueWorker import QueueWorker
from wrappers.api.wynncraft.v3.types import PlayerStats

_online_players: set[str] = set()
_players_to_track: asyncio.Queue[str] = asyncio.Queue()
_worker = QueueWorker(delay=0.1)


async def _record_stats(uuid: str, retried: bool = False):
    if wrappers.api.wynncraft.v3.session.calculate_remaining_requests() < 10:
        wait_time = wrappers.api.wynncraft.v3.session.ratelimit_reset_time()
        await asyncio.sleep(wait_time + 1)

    stats = None
    try:
        stats: PlayerStats = await wrappers.api.wynncraft.v3.player.stats(uuid=uuid)
        await wrappers.storage.playerTrackerData.add_record(stats)
    except wrappers.api.wynncraft.v3.player.UnknownPlayerException:
        handlers.logging.debug(f"Couldn't get stats of player with uuid {uuid}: Unknown player.")
    except aiohttp.client_exceptions.ClientResponseError as e:
        if e.status == 500:
            handlers.logging.warning(f"Error 500 for player with uuid: {uuid}")
        elif not retried:
            await asyncio.sleep(1)
            await _record_stats(uuid, True)
        else:
            handlers.logging.error(f"Client error in player stat tracker: uuid: {uuid}")
            raise e
    except Exception as e:
        handlers.logging.error(f"Exception in player stat tracker: uuid: {uuid}, stats: {stats}")
        raise e


@tasks.loop(seconds=61, reconnect=True)
async def _update_online():
    try:
        global _online_players, _players_to_track
        prev_online_players = _online_players
        _online_players = (await wrappers.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.UUID)).keys()

        left_players = prev_online_players - _online_players

        [_worker.put(_record_stats, name) for name in left_players]

        if len(left_players) >= 50:
            handlers.logging.debug(f"Tracking {len(left_players)} player's stats.")
    except handlers.rateLimit.RateLimitException:
        pass
    except Exception as ex:
        await handlers.logging.error(exc_info=ex)
        raise ex


_update_online.add_exception_type(
    aiohttp.client_exceptions.ClientError,
    Exception
)


def start():
    _update_online.start()
    _worker.start()
    handlers.logging.info("Stat Tracker workers started.")


def stop():
    _worker.stop()
    _update_online.stop()
