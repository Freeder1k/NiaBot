import asyncio

import discord.utils
from discord.utils import MaybeAwaitableFunc, P, T

import handlers.logging

_online_players: set[str] = set()
_players_to_track: asyncio.Queue[str] = asyncio.Queue()


class QueueWorker:
    def __init__(self, delay: float = 0.0):
        """
        A worker that processes tasks from a queue.
        Errors are tracked and the delay between tasks is increased exponentially if consecutive errors occur.

        :param delay: The time in seconds to wait between tasks
        """
        self._queue = asyncio.Queue()
        self._error_count = 0
        self._delay = delay
        self._task: asyncio.Task = None

    async def _worker(self):
        stopped = False
        while True:
            try:
                await asyncio.sleep((2 ** self._error_count) - 1)
                task, args, kwargs = await self._queue.get()

                await discord.utils.maybe_coroutine(task, *args, **kwargs)

                if self._error_count > 0:
                    self._error_count -= 1

                await asyncio.sleep(self._delay)
            except (KeyboardInterrupt, SystemExit, asyncio.CancelledError) as e:
                stopped = True
                raise e
            except Exception as ex:
                handlers.logging.error(exc_info=ex)
                if self._error_count < 12:
                    self._error_count += 1
            finally:
                self._queue.task_done()

    def put(self, f: MaybeAwaitableFunc[P, T], *args: P.args, **kwargs: P.kwargs):
        """
        Add a task to the queue for execution.

        :param f: The function to call. Can be either a coroutine or a regular function.
        :param args: The arguments to pass to the function.
        :param kwargs: The keyword arguments to pass to the function.
        """
        self._queue.put_nowait((f, args, kwargs))

    async def join(self):
        """
        Block until all items in the queue have been gotten and processed.
        The count of unfinished tasks goes up whenever an item is added to the queue.
        The count goes down whenever a task is completed.
        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        await self._queue.join()

    def qsize(self):
        """
        Number of items in the queue.
        """
        return self._queue.qsize()

    def empty(self):
        """
        Return True if the queue is empty, False otherwise.
        """
        return self._queue.empty()

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
