import asyncio

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
from common.types.enums import PlayerIdentifier


class PlayerQueueWorker:
    def __init__(self, delay=0.01):
        """
        QueueWorker for player stats.
        """
        self._queue = asyncio.Queue()
        self._error_count = 0
        self._delay = delay
        self._task: asyncio.Task = None
        self._delayed_tasks = set()

    async def _record_stats(self, uuid: str, tries: int):
        if common.api.wynncraft.v3.session.calculate_remaining_requests() < 10:
            wait_time = common.api.wynncraft.v3.session.ratelimit_reset_time()
            await asyncio.sleep(wait_time + 1)

        stats = None
        try:
            stats = await common.api.wynncraft.v3.player.stats(uuid=uuid)
            # TODO track name changes
            await common.storage.playerTrackerData.add_record(stats)
        except common.api.wynncraft.v3.player.UnknownPlayerException:
            common.logging.debug(f"Couldn't get stats of player with uuid {uuid}: Unknown player.")
        except aiohttp.client_exceptions.ClientResponseError as e:
            if e.status == 500:
                common.logging.warning(f"Error 500 for player with uuid: {uuid}")
            elif tries < 1:
                self.put_delayed(delay=30, uuid=uuid, tries=tries + 1)
            else:
                common.logging.error(f"Client error in player stat tracker: uuid: {uuid}")
                raise e
        except Exception as e:
            common.logging.error(f"Exception in player stat tracker: uuid: {uuid}, stats: {stats}")
            raise e

    async def _worker(self):
        while True:
            try:
                await asyncio.sleep((2 ** self._error_count) - 1)

                # wait if we're close to the ratelimit
                if common.api.wynncraft.v3.session.calculate_remaining_requests() < 10:
                    wait_time = common.api.wynncraft.v3.session.ratelimit_reset_time()
                    await asyncio.sleep(wait_time + 1)

                uuid, tries = await self._queue.get()

                try:
                    await self._record_stats(uuid, tries)
                finally:
                    self._queue.task_done()

                if self._error_count > 0:
                    self._error_count -= 1

                await asyncio.sleep(self._delay)
            except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
                raise e
            except Exception as ex:
                common.logging.error(exc_info=ex)
                if self._error_count < 12:
                    self._error_count += 1

    def put(self, uuid, tries=0):
        """
        Add a player to the queue for stat tracking.
        """
        self._queue.put_nowait((uuid, tries))

    async def _put_delayed(self, delay, uuid, tries=0):
        await asyncio.sleep(delay)
        self.put(uuid, tries)

    def put_delayed(self, delay, uuid, tries=0):
        """
        Add a player to the queue for stat tracking after a delay.
        """
        task = asyncio.create_task(self._put_delayed(delay, uuid, tries))

        # Keep a reference to the task to prevent it from being garbage collected
        self._delayed_tasks.add(task)
        task.add_done_callback(self._delayed_tasks.discard)

    async def join(self):
        """
        Block until all players in the queue have been processed.
        """
        await self._queue.join()

    def qsize(self):
        """
        Number of players in the queue.
        """
        return self._queue.qsize()

    def empty(self):
        """
        Return True if the queue is empty, False otherwise.
        """
        return self._queue.empty()

    @property
    def started(self):
        """
        Return True if the worker is running, False otherwise.
        """
        return self._task is not None

    def start(self):
        """
        Start the worker.
        """
        if self._task is not None:
            raise RuntimeError("Worker already running")
        self._task = asyncio.create_task(self._worker())

    def stop(self):
        """
        Stop the worker.
        """
        if self._task is not None:
            self._task.cancel()
        self._error_count = 0
        self._task = None


_online_players: set[str] = set()
_worker = PlayerQueueWorker()


@tasks.loop(seconds=61, reconnect=True)
async def _update_online():
    try:
        global _online_players
        prev_online_players = _online_players
        _online_players = set(
            (await common.api.wynncraft.v3.player.player_list(identifier=PlayerIdentifier.UUID)).keys())

        joined_players = _online_players - prev_online_players
        left_players = prev_online_players - _online_players

        for uuid in joined_players:
            _worker.put(uuid)
        for uuid in left_players:
            _worker.put(uuid)

        if _worker.qsize() >= 50:
            common.logging.debug(f"Tracking {len(left_players)}({_worker.qsize()}) player's stats.")
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
